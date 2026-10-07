import json

import pytest
import requests

import llm_client

FAKE = {"message": {"content": "Paris."}, "done": True}


def read_last(folder):
    lines = (folder / "raw_outputs.jsonl").read_text(encoding="utf-8").strip().splitlines()
    return json.loads(lines[-1])


def test_ask_writes_record(monkeypatch, runs_dir):
    def fake_chat(payload, meta):
        meta["attempts"] = 2
        return FAKE

    monkeypatch.setattr(llm_client, "_chat", fake_chat)

    assert llm_client.ask("capital of France?") == "Paris."
    rec = read_last(runs_dir)
    assert rec["kind"] == "ask"
    assert rec["attempts"] == 2
    assert rec["temperature"] == 0.0
    assert rec["response"] == FAKE
    assert rec["error"] is None


def test_ask_logs_error_and_reraises(monkeypatch, runs_dir):
    def fake_chat(payload, meta):
        meta["attempts"] = 3
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setattr(llm_client, "_chat", fake_chat)

    with pytest.raises(requests.exceptions.Timeout):
        llm_client.ask("x")
    rec = read_last(runs_dir)
    assert rec["attempts"] == 3
    assert rec["response"] is None
    assert "Timeout" in rec["error"]