import functools
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pydantic import ValidationError

log = logging.getLogger(__name__)

RETRYABLE = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LLM_MODEL", "llama3.2:3b")
RUNS_DIR = Path("runs")


def with_retries(max_attempts=3, base_delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE as exc:
                    if attempt == max_attempts:
                        raise
                    delay = base_delay * 2 ** (attempt - 1)
                    log.warning("retry %d/%d after %s: %s (waiting %.1fs)",
                                attempt, max_attempts, type(exc).__name__, exc, delay)
                    time.sleep(delay)
        return wrapper
    return decorator


def save_run(record: dict) -> None:
    RUNS_DIR.mkdir(exist_ok=True)
    with open(RUNS_DIR / "raw_outputs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _log_run(kind, prompt, temperature, meta, started, response=None, parsed=None, error=None):
    save_run({
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "model": MODEL,
        "temperature": temperature,
        "prompt": prompt,
        "attempts": meta["attempts"],
        "duration_s": round(time.perf_counter() - started, 3),
        "response": response,
        "parsed": parsed,
        "error": error,
    })


def normalize(text: str) -> str:
    return text.strip().strip(".!?\"' ").lower()


@with_retries(max_attempts=3)
def _chat(payload: dict, meta: dict) -> dict:
    meta["attempts"] += 1
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def ask(prompt: str, temperature: float = 0.0) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    meta = {"attempts": 0}
    started = time.perf_counter()
    try:
        data = _chat(payload, meta)
    except Exception as exc:
        _log_run("ask", prompt, temperature, meta, started, error=repr(exc))
        raise
    _log_run("ask", prompt, temperature, meta, started, response=data)
    return data["message"]["content"]


def ask_structured(prompt: str, model_class, temperature: float = 0.0):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": model_class.model_json_schema(),
        "options": {"temperature": temperature},
    }
    meta = {"attempts": 0}
    started = time.perf_counter()
    try:
        data = _chat(payload, meta)
    except Exception as exc:
        _log_run("ask_structured", prompt, temperature, meta, started, error=repr(exc))
        raise
    try:
        result = model_class.model_validate_json(data["message"]["content"])
    except ValidationError as exc:
        _log_run("ask_structured", prompt, temperature, meta, started, response=data, error=repr(exc))
        raise
    _log_run("ask_structured", prompt, temperature, meta, started, response=data, parsed=result.model_dump())
    return result