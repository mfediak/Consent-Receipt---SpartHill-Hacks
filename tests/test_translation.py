import json

import pytest
from fastapi.testclient import TestClient

from app import translation
from app.translation import TranslationRequest
from app.main import app


def request():
    return TranslationRequest.model_validate({
        "language": "es",
        "overview": "The policy explains data use.",
        "disclaimer": "This is not legal advice.",
        "category_labels": {"data_usage": "How they use it"},
        "status_labels": {"disclosed": "Disclosed"},
        "ui_labels": {"listen": "Listen to summary"},
        "disclosures": [{"category": "data_usage", "summary": "They use account data."}],
    })


def test_translation_preserves_categories_and_label_keys(monkeypatch):
    monkeypatch.setattr(translation, "active_providers", lambda: ["groq"])
    monkeypatch.setattr(translation, "models_for", lambda provider: ["test-model"])
    prompts = []
    translated = {
        "overview": "La política explica el uso de datos.",
        "disclaimer": "Esto no es asesoramiento legal.",
        "category_labels": {"data_usage": "Cómo usan los datos"},
        "status_labels": {"disclosed": "Divulgado"},
        "ui_labels": {"listen": "Escuchar el resumen"},
        "disclosures": [{"category": "data_usage", "summary": "Usan los datos de la cuenta."}],
    }
    monkeypatch.setattr(translation, "_generate", lambda provider, model, prompt: prompts.append(prompt) or json.dumps(translated))

    result = translation.translate_receipt(request())

    assert "Spanish" in prompts[0]
    assert result["disclosures"][0]["category"] == "data_usage"
    assert result["disclosures"][0]["summary"] == "Usan los datos de la cuenta."


def test_translation_rejects_changed_category_ids(monkeypatch):
    monkeypatch.setattr(translation, "active_providers", lambda: ["groq"])
    monkeypatch.setattr(translation, "models_for", lambda provider: ["test-model"])
    changed = {
        "overview": "Resumen", "disclaimer": "Aviso",
        "category_labels": {"data_usage": "Uso"}, "status_labels": {"disclosed": "Divulgado"},
        "ui_labels": {"listen": "Escuchar"},
        "disclosures": [{"category": "uso_de_datos", "summary": "Resumen traducido"}],
    }
    monkeypatch.setattr(translation, "_generate", lambda *args: json.dumps(changed))

    with pytest.raises(translation.ProviderError, match="changed disclosure categories"):
        translation.translate_receipt(request())


def test_translation_requires_configured_provider(monkeypatch):
    monkeypatch.setattr(translation, "active_providers", lambda: [])

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        translation.translate_receipt(request())


def test_translation_endpoint_returns_translated_result(monkeypatch):
    translated = {
        "overview": "Resumen traducido", "disclaimer": "Aviso traducido",
        "category_labels": {"data_usage": "Uso"}, "status_labels": {"disclosed": "Divulgado"},
        "ui_labels": {"listen": "Escuchar"},
        "disclosures": [{"category": "data_usage", "summary": "Resumen de categoría"}],
    }
    monkeypatch.setattr("app.main.translate_receipt", lambda body: translated)

    response = TestClient(app).post("/api/translate", json=request().model_dump())

    assert response.status_code == 200
    assert response.json()["disclosures"][0]["summary"] == "Resumen de categoría"