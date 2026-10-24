import json
import pytest
from app import analyzer as a

REPLY = json.dumps({"company": "X", "overview": "o", "disclosures": [
    {"category": "data_sharing", "summary": "s", "evidence": "We do not sell your personal information.", "status": "disclosed"}]})


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("GROQ_API_KEY", "GROQ_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(a.time, "sleep", lambda s: None)
    monkeypatch.setattr(a, "load_dotenv", lambda: None)


def test_no_keys_raises_clear_error():
    with pytest.raises(RuntimeError, match="No valid Groq API key"):
        a.analyze_policy("x" * 300)


def test_example_key_is_not_configured(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", a.EXAMPLE_API_KEY)
    assert a.active_providers() == []


def test_default_model_is_available_groq_model():
    assert a.models_for("groq") == ["openai/gpt-oss-20b"]


def test_provider_setting_cannot_enable_non_groq_backends(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("PROVIDERS", "other,not-a-provider")
    assert a.active_providers() == ["groq"]


def test_generate_sends_groq_bearer_token(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    requests = []

    class Response:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "{}"}}]}

    def fake_post(url, *, json, headers, timeout):
        requests.append((url, headers))
        return Response()

    monkeypatch.setattr(a.httpx, "post", fake_post)

    assert a._generate("groq", "test-model", "prompt") == "{}"
    assert requests[0][1]["Authorization"] == "Bearer test-key"


def test_retries_groq_when_rate_limited(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    calls = []

    def fake(provider, model, prompt):
        calls.append(provider)
        if len(calls) == 1:
            raise a.ProviderError("HTTP 429: rate limit")
        return "```json\n" + REPLY + "\n```"
    monkeypatch.setattr(a, "_generate", fake)
    analysis, used = a.analyze_policy("x" * 300)
    assert used.startswith("groq/") and calls == ["groq", "groq"]


def test_bad_json_reports_groq_failure(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(a, "_generate", lambda *x: "I cannot help with that")
    with pytest.raises(a.ProviderError, match="groq/"):
        a.analyze_policy("x" * 300)
