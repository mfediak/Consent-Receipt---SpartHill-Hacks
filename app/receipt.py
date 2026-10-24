import hashlib
from datetime import datetime, timezone
from .models import CATEGORIES, PolicyAnalysis
from .verification import find_evidence

DISCLAIMER = (
    "This is an AI-assisted disclosure review, not legal advice or a legal certification. "
    "Verified means the quoted text exists in the policy; it does not guarantee the summary "
    "interprets it correctly. Read the highlighted passages yourself."
)


def build_receipt(policy_text: str, analysis: PolicyAnalysis, model: str) -> dict:
    by_cat = {d.category: d for d in analysis.disclosures}
    items = []
    for cat in CATEGORIES:  # always exactly five, in a fixed order
        d = by_cat.get(cat)
        if d is None:
            items.append({"category": cat, "summary": "The analysis returned nothing for this category.",
                          "evidence": "", "status": "not_found", "evidence_verified": None, "span": None})
            continue
        span = find_evidence(policy_text, d.evidence) if d.evidence else None
        item = d.model_dump()
        item["evidence_verified"] = (span is not None) if d.evidence else None
        item["span"] = list(span) if span else None
        items.append(item)
    checked = [i for i in items if i["evidence_verified"] is not None]
    return {
        "company": analysis.company,
        "overview": analysis.overview,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "policy_sha256": hashlib.sha256(policy_text.encode("utf-8")).hexdigest(),
        "model": model,
        "disclosures": items,
        "stats": {"quotes_checked": len(checked),
                  "quotes_verified": sum(1 for i in checked if i["evidence_verified"])},
        "disclaimer": DISCLAIMER,
    }
