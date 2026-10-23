"""Build the downloadable privacy disclosure receipt. Pure Python."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .constants import CATEGORIES, NOTICE, STATUS
from .verification import policy_fingerprint

RECEIPT_VERSION = "1.0"


def count_statuses(findings: list[dict]) -> dict:
    counts = {key: 0 for key in STATUS}
    for finding in findings:
        counts[finding["status"]] += 1
    return counts


def build_receipt(
    *,
    company: str,
    source: str,
    policy_text: str,
    findings: list[dict],
    model: str,
    elapsed_seconds: float,
    analyzed_at: datetime | None = None,
) -> dict:
    """Turn verified findings into the receipt object.

    The receipt stores a fingerprint of the policy, not the policy itself, so it
    can later be matched against the same text without keeping a copy of it.
    """
    when = (analyzed_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    quotes_expected = [f for f in findings if f["model_status"] in ("disclosed", "unclear")]
    quotes_verified = [f for f in quotes_expected if f["evidence_verified"] is True]

    disclosures = []
    for f in findings:
        location = None
        if f["start"] is not None:
            location = {"paragraph": f["paragraph_id"], "start": f["start"], "end": f["end"]}
        disclosures.append(
            {
                "category": f["category"],
                "status": f["status"],
                "model_status": f["model_status"],
                "summary": f["summary"],
                "evidence": f["evidence"],
                "evidence_verified": f["evidence_verified"],
                "match_type": f["match_type"],
                "source_location": location,
            }
        )

    return {
        "receipt_type": "privacy_policy_disclosure_review",
        "version": RECEIPT_VERSION,
        "company": company.strip() or None,
        "policy_source": source.strip() or None,
        "policy_sha256": policy_fingerprint(policy_text),
        "policy_characters": len(policy_text),
        "analyzed_at": when.isoformat(timespec="seconds"),
        "model": model,
        "processing_seconds": round(elapsed_seconds, 1),
        "summary": {
            **count_statuses(findings),
            "quotes_checked": len(quotes_expected),
            "quotes_verified": len(quotes_verified),
        },
        "disclosures": disclosures,
        "notice": NOTICE,
    }


def receipt_to_json(receipt: dict) -> str:
    return json.dumps(receipt, indent=2, ensure_ascii=False)


def receipt_to_text(receipt: dict, titles: dict[str, str] | None = None) -> str:
    """Plain-text version for people who do not want JSON."""
    titles = titles or {k: v["title"] for k, v in CATEGORIES.items()}
    lines = [
        "PRIVACY DISCLOSURE RECEIPT",
        f"Company or product: {receipt['company'] or 'Not given'}",
        f"Policy source: {receipt['policy_source'] or 'Not given'}",
        f"Analyzed: {receipt['analyzed_at']} with {receipt['model']}",
        f"Policy fingerprint (SHA-256): {receipt['policy_sha256']}",
        "",
    ]
    for d in receipt["disclosures"]:
        lines.append(f"{titles[d['category']]}: {STATUS[d['status']]['label']}")
        lines.append(f"  Summary: {d['summary']}")
        if d["evidence"]:
            where = ""
            if d["source_location"] and d["source_location"]["paragraph"]:
                where = f" (paragraph {d['source_location']['paragraph'][1:]})"
            check = "found in policy" if d["evidence_verified"] else "NOT found in policy"
            lines.append(f"  Quote, {check}{where}: \"{d['evidence']}\"")
        lines.append("")
    s = receipt["summary"]
    lines.append(
        f"Quotes found in the policy: {s['quotes_verified']} of {s['quotes_checked']}."
    )
    lines.append("")
    lines.append(receipt["notice"])
    return "\n".join(lines) + "\n"
