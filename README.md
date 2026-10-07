# llm-test-harness

A small pytest harness for testing a **local LLM** (Ollama, `llama3.2:3b`) the way you would test any other system: known-answer checks, schema validation, retries for infrastructure failures, and a raw-output log of every call.

Everything runs locally and offline-capable. No API keys, no paid services, no external data.

## Run it

```powershell
git clone https://github.com/stealthy1992/llm-test-harness.git
cd llm-test-harness
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2:3b

pytest -q                    # everything (needs Ollama running)
pytest -m "not live" -q      # offline tests only (no Ollama needed)
pytest -m live -q            # live tests only
```

Tested with Python 3.12 on Windows 10. If Ollama is not reachable, live tests are **skipped**, not failed. A skipped test means "no evidence", so check the skipped count before trusting a green run.

## Results (single run, temperature 0.0)

| Suite | Tests | Needs Ollama | Result |
|---|---|---|---|
| Schema rejection (`BugTriage`) | 3 | No | 3 passed |
| Retry logic (fake failing functions) | 3 | No | 3 passed |
| Run-log writing | 2 | No | 2 passed |
| Basics + structured output | 8 | Yes | 8 passed |
| Data-driven facts (`cases/facts.json`) | 10 | Yes | 10 passed |
| Data-driven bug triage (`cases/triage.json`) | 10 | Yes | 9 passed, **1 xfailed** |

Total: **35 passed, 1 xfailed** (36 tests, about 2 minutes on a GTX 970M).

### Known model failure

`sql-error`: for the report *"The search box accepts SQL fragments and returns raw database errors."*, `llama3.2:3b` returns `severity: high` and a summary that says "SQL injection vulnerability", but sets `is_security_issue: false`. The output is valid structure and an internally contradictory answer.

The test is marked `xfail(strict=True)` with the reason recorded in `cases/triage.json`. I did not loosen the assertion. If the case ever starts passing (different model, different prompt), the suite fails and tells me to remove the marker.

## How it works

```
llm_client.py        ask(), ask_structured(), retry decorator, JSONL run log
schemas.py           BugTriage (pydantic): severity Literal, component, is_security_issue, summary
conftest.py          fixtures: temp run-log folder, skip live tests if Ollama is down
cases/*.json         test data (prompt + expected value), loaded by tests/test_cases.py
tests/               pytest suites
runs/                raw outputs (git-ignored)
```

- **Retries:** exponential backoff (1s, 2s) on connection errors and timeouts only. Wrong answers and validation errors are never retried, because that would hide model quality problems.
- **Structured output:** the pydantic JSON schema is sent to Ollama's `format` field, and the reply is validated again on return. Valid structure does not mean a correct answer.
- **Raw-output log:** every call appends one JSON line to `runs/raw_outputs.jsonl`.

```json
{
  "ts": "2026-10-07T12:54:06+00:00",
  "kind": "ask_structured",
  "model": "llama3.2:3b",
  "temperature": 0.0,
  "prompt": "...",
  "attempts": 1,
  "duration_s": 7.101,
  "response": { "message": { "content": "..." }, "eval_count": 37, "total_duration": 5050421500 },
  "parsed": { "severity": "low", "component": "footer", "is_security_issue": false, "summary": "..." },
  "error": null
}
```

`attempts` above 1 means a call was silently retried. Retry warnings are also printed live during test runs.

## Add a test case

Append an object to `cases/facts.json` or `cases/triage.json`. No Python changes are needed.

## Limitations

- 20 data-driven prompts, one small model, one run per case. These are smoke-level checks, not statistically meaningful quality measurements. Run-to-run variance is not measured yet.
- Temperature 0.0 gives repeatable output on this setup but is not a guarantee across hardware or Ollama versions.
- HTTP 5xx and 429 responses are not retried yet; only connection errors and timeouts are.
- Exact-match assertions after light normalisation suit short factual answers. They do not suit open-ended text.
- No LLM-as-judge or human-labelled dataset in this repo.
