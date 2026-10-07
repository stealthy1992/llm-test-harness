import json
from pathlib import Path

import pytest

from llm_client import ask, ask_structured, normalize
from schemas import BugTriage

CASES_DIR = Path(__file__).parent.parent / "cases"


def load(name):
    return json.loads((CASES_DIR / name).read_text(encoding="utf-8"))


FACTS = load("facts.json")
TRIAGE = load("triage.json")

pytestmark = pytest.mark.live


def params(cases):
    return [
        pytest.param(
            c,
            id=c["id"],
            marks=pytest.mark.xfail(reason=c["known_failure"], strict=True)
            if "known_failure" in c
            else (),
        )
        for c in cases
    ]


@pytest.mark.parametrize("case", params(FACTS))
def test_fact(case):
    assert normalize(ask(case["prompt"])) == case["expected"]


@pytest.mark.parametrize("case", params(TRIAGE))
def test_triage_security_flag(case):
    prompt = f"Triage this bug report. Reply with JSON only.\nBug report: {case['report']}"
    result = ask_structured(prompt, BugTriage)
    assert result.is_security_issue is case["security"]