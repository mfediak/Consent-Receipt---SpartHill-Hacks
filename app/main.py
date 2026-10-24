import os
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .analyzer import ProviderError, active_providers, analyze_policy
from .documents import DocumentError, extract_policy_text
from .receipt import build_receipt
from .report import PolicyReport, build_report_pdf
from .translation import TranslationRequest, translate_receipt

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
MAX_CHARS, MIN_CHARS = 60_000, 200
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(title="ConsentReceipt")


class AnalyzeRequest(BaseModel):
    policy_text: str


@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is over 10 MB. Choose a smaller policy file.")
    try:
        text = extract_policy_text(file.filename or "", payload)
    except DocumentError as e:
        raise HTTPException(400, str(e))
    if len(text) > MAX_CHARS:
        raise HTTPException(413, f"Policy is over {MAX_CHARS:,} characters. Choose a shorter file.")
    return {"policy_text": text, "file_name": file.filename or "Uploaded file"}


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


@app.post("/api/report")
def report(body: PolicyReport):
    pdf = build_report_pdf(body)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="consent-receipt.pdf"'})


@app.post("/api/translate")
def translate(body: TranslationRequest):
    try:
        return translate_receipt(body)
    except Exception as e:
        status, message = explain(e)
        raise HTTPException(status, message)


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
