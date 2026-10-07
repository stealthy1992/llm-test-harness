import pytest
from pydantic import ValidationError
from llm_client import ask_structured
from schemas import BugTriage

PROMPT = "Triage this bug report. Reply with JSON only.\nBug report: {report}"


# Offline checks: no model involved. They prove the schema itself rejects bad data.
def test_schema_rejects_unknown_severity():
    with pytest.raises(ValidationError):
        BugTriage(severity="urgent", component="login",
                  is_security_issue=False, summary="x")


def test_schema_rejects_missing_field():
    with pytest.raises(ValidationError):
        BugTriage(severity="low", component="login")


def test_schema_rejects_wrong_type():
    with pytest.raises(ValidationError):
        BugTriage(severity="low", component="login",
                  is_security_issue="maybe", summary="x")


# Live checks: these call your local model.
@pytest.mark.live
def test_triage_returns_valid_structure():
    report = "The checkout page shows a blank screen after clicking Pay."
    result = ask_structured(PROMPT.format(report=report), BugTriage)
    print(result.model_dump_json(indent=2))
    assert isinstance(result, BugTriage)
    assert result.summary.strip() != ""

@pytest.mark.live
@pytest.mark.parametrize("report, expected_security", [
    ("Users can view other customers' order history by changing the order ID in the URL.", True),
    ("The footer link color is slightly different from the design on the About page.", False),
])

@pytest.mark.live
def test_security_flag(report, expected_security):
    result = ask_structured(PROMPT.format(report=report), BugTriage)
    assert result.is_security_issue == expected_security