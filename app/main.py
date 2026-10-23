import os
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .analyzer import ProviderError, active_providers, analyze_policy
from .receipt import build_receipt

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
MAX_CHARS, MIN_CHARS = 60_000, 200

app = FastAPI(title="ConsentReceipt")


class AnalyzeRequest(BaseModel):
    policy_text: str


@app.get("/api/health")
def health():
    providers = active_providers()
    return {"ok": True, "key_configured": bool(providers), "providers": providers, "max_chars": MAX_CHARS}


@app.get("/api/sample")
def sample():
    return {"policy_text": (ROOT / "samples" / "sample_policy.txt").read_text(encoding="utf-8").strip()}


def explain(e: Exception) -> tuple[int, str]:
    """Turn an error into a (status, message) people can act on."""
    if isinstance(e, RuntimeError):
        return 500, str(e)
    msg = str(e)
    if isinstance(e, ProviderError):
        hint = " Rate limit or overload: wait a minute and retry." if ("429" in msg or "503" in msg) else ""
        return 502, f"Groq request failed. {msg[:450]}{hint}"
    return 502, f"Something went wrong: {msg[:300]}"


@app.post("/api/analyze")
def analyze(body: AnalyzeRequest):
    text = body.policy_text.strip()
    if len(text) < MIN_CHARS:
        raise HTTPException(400, "That looks too short to be a privacy policy. Paste the full text.")
    if len(text) > MAX_CHARS:
        raise HTTPException(413, f"Policy is over {MAX_CHARS:,} characters. Paste a shorter section.")
    try:
        analysis, used_model = analyze_policy(text)
        receipt = build_receipt(text, analysis, used_model)
    except Exception as e:
        traceback.print_exc()
        status, message = explain(e)
        raise HTTPException(status, message)
    receipt["policy_text"] = text  # lets the UI highlight quotes; stripped from downloads
    return receipt


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
