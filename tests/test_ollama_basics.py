import pytest
from llm_client import ask, normalize

pytestmark = pytest.mark.live


def test_model_replies():
    reply = ask("Reply with the single word: pong")
    assert reply.strip() != ""


@pytest.mark.parametrize("prompt, expected", [
    ("What is 2 + 2? Answer with just the number.", "4"),
    ("What is the capital of France? One word.", "paris"),
    ("What is the capital of Japan? One word.", "tokyo"),
])
def test_basic_facts(prompt, expected):
    assert normalize(ask(prompt)) == expected

def test_same_prompt_same_answer():
    prompt = "Write a one-sentence slogan for a coffee shop."
    replies = [ask(prompt, temperature=0.0) for _ in range(5)]
    for r in replies:
        print(r)
    assert len(set(replies)) == 1