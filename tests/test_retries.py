import pytest
import requests

from llm_client import with_retries


def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = {"n": 0}

    @with_retries(max_attempts=3)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.exceptions.ConnectionError("down")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = {"n": 0}

    @with_retries(max_attempts=3)
    def always_down():
        calls["n"] += 1
        raise requests.exceptions.Timeout("slow")

    with pytest.raises(requests.exceptions.Timeout):
        always_down()
    assert calls["n"] == 3


def test_does_not_retry_other_errors(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = {"n": 0}

    @with_retries(max_attempts=3)
    def bad_logic():
        calls["n"] += 1
        raise ValueError("not a network problem")

    with pytest.raises(ValueError):
        bad_logic()
    assert calls["n"] == 1