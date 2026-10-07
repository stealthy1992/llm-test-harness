import pytest
import requests

import llm_client


@pytest.fixture
def runs_dir(monkeypatch, tmp_path):
    """Redirect run logs to a temp folder for this test."""
    monkeypatch.setattr(llm_client, "RUNS_DIR", tmp_path)
    return tmp_path


@pytest.fixture(scope="session")
def ollama_up():
    """Checked once per session; skips the requesting test if Ollama is unreachable."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2).raise_for_status()
    except requests.exceptions.RequestException:
        pytest.skip("Ollama not reachable")


@pytest.fixture(autouse=True)
def _live_tests_need_ollama(request):
    """Runs for every test; only acts on tests marked live."""
    if request.node.get_closest_marker("live"):
        request.getfixturevalue("ollama_up")