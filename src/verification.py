"""Source-text preparation and evidence checking.

Pure Python: no network and no AI. Nothing the model says is trusted until it
has passed through verify_disclosures().
"""

from __future__ import annotations

import hashlib
import re

from .constants import CATEGORIES, CATEGORY_ORDER

# A quote shorter than this proves almost nothing (it could match anywhere).
MIN_EVIDENCE_CHARS = 12

_APOSTROPHES = "'\u2018\u2019\u02bc"
_DOUBLE_QUOTES = '"\u201c\u201d'


# --- Step 2: prepare and label the source text -------------------------------

def normalize_policy(text: str) -> str:
    """Unify line endings and trim trailing spaces. Does not change any words."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def policy_fingerprint(text: str) -> str:
    """SHA-256 of the normalized policy text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _spans(text: str, separator: str) -> list[tuple[int, int]]:
    spans, pos = [], 0
    for match in re.finditer(separator, text):
        spans.append((pos, match.start()))
        pos = match.end()
    spans.append((pos, len(text)))
    return spans


def split_paragraphs(text: str) -> list[dict]:
    """Label paragraphs P1, P2, ... with their character offsets in `text`.

    Splits on blank lines. If the text has none, falls back to single line breaks.
    """
    spans = _spans(text, r"\n[ \t]*\n")
    if len(spans) <= 1:
        spans = _spans(text, r"\n")
    paragraphs: list[dict] = []
    for start, end in spans:
        chunk = text[start:end]
        lead = len(chunk) - len(chunk.lstrip())
        s, e = start + lead, start + len(chunk.rstrip())
        if e > s:
            paragraphs.append({"id": f"P{len(paragraphs) + 1}", "start": s, "end": e})
    return paragraphs


def paragraph_for(paragraphs: list[dict], position: int) -> str | None:
    found = None
    for p in paragraphs:
        if p["start"] <= position:
            found = p["id"]
        else:
            break
    return found


# --- Step 4: verify the model's quotes ---------------------------------------

def _clean_evidence(evidence: str) -> str:
    # Models sometimes wrap a quote in quotation marks. A substring of the policy
    # still matches without them, so stripping can only help.
    return (evidence or "").strip().strip(_DOUBLE_QUOTES).strip()


def _char_pattern(char: str) -> str:
    if char in _APOSTROPHES:
        return f"[{_APOSTROPHES}]"
    if char in _DOUBLE_QUOTES:
        return f"[{_DOUBLE_QUOTES}]"
    return re.escape(char)


def _evidence_pattern(evidence: str) -> str:
    parts = []
    for token in re.split(r"(\s+)", evidence):
        if not token:
            continue
        parts.append(r"\s+" if token.isspace() else "".join(_char_pattern(c) for c in token))
    return "".join(parts)


def locate_evidence(policy_text: str, evidence: str) -> dict | None:
    """Find `evidence` in `policy_text`.

    Tries an exact match first, then a match that ignores line breaks, repeated
    spaces and straight-versus-curly quotes. Every word must still match.
    Returns {"start", "end", "match_type"} or None.
    """
    quote = _clean_evidence(evidence)
    if len(quote) < MIN_EVIDENCE_CHARS:
        return None
    index = policy_text.find(quote)
    if index >= 0:
        return {"start": index, "end": index + len(quote), "match_type": "exact"}
    match = re.search(_evidence_pattern(quote), policy_text)
    if match:
        return {"start": match.start(), "end": match.end(), "match_type": "normalized"}
    return None


def verify_disclosures(policy_text: str, disclosures: list[dict]) -> list[dict]:
    """Check every quote and assign the final status.

    Returns exactly five findings in category order. Final status is one of
    disclosed, unclear, not_found, or verification_failed.
    """
    paragraphs = split_paragraphs(policy_text)
    by_category: dict[str, dict] = {}
    for item in disclosures:
        by_category.setdefault(item.get("category"), item)

    findings = []
    for key in CATEGORY_ORDER:
        meta = CATEGORIES[key]
        item = by_category.get(key)
        finding = {
            "category": key,
            "title": meta["title"],
            "question": meta["question"],
            "tag": meta["tag"],
            "summary": "",
            "evidence": "",
            "model_status": item.get("status") if item else None,
            "status": "verification_failed",
            "evidence_verified": False,
            "match_type": None,
            "paragraph_id": None,
            "start": None,
            "end": None,
            "note": "",
        }

        if item is None:
            finding["summary"] = "The analysis returned nothing for this category."
            finding["note"] = "No result came back for this category. Run the analysis again."
            findings.append(finding)
            continue

        finding["summary"] = (item.get("summary") or "").strip()
        quote = (item.get("evidence") or "").strip()
        model_status = item.get("status")

        if model_status == "not_found":
            finding.update(
                status="not_found",
                evidence_verified=None,  # nothing to verify
                note="No quote to check. The policy does not address this.",
            )
        elif not quote:
            finding["note"] = "The model gave no supporting quote, so this cannot be verified."
        else:
            hit = locate_evidence(policy_text, quote)
            if hit:
                finding.update(
                    status=model_status if model_status in ("disclosed", "unclear") else "unclear",
                    evidence=policy_text[hit["start"]:hit["end"]],  # the policy's own text
                    evidence_verified=True,
                    match_type=hit["match_type"],
                    paragraph_id=paragraph_for(paragraphs, hit["start"]),
                    start=hit["start"],
                    end=hit["end"],
                    note="Found in the policy.",
                )
            else:
                finding["evidence"] = quote
                finding["note"] = (
                    "This quote does not appear in the policy text. "
                    "Do not rely on the summary."
                    if len(_clean_evidence(quote)) >= MIN_EVIDENCE_CHARS
                    else "The quote is too short to prove anything."
                )
        findings.append(finding)
    return findings
