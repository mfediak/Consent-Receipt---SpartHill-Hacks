"""Run ConsentReceipt against the labeled fictional policies and print metrics.

Usage:  python -m scripts.evaluate
Needs GROQ_API_KEY. Pauses between calls to respect free-tier rate limits.
"""
import json, re, sys, time
from pathlib import Path
from app.analyzer import analyze_policy
from app.receipt import build_receipt

ROOT = Path(__file__).resolve().parent.parent / "eval"
SELL = re.compile(r"\b(sell|sells|selling|sold)\b", re.I)
NEG = re.compile(r"\b(not|never|no|doesn't|does not|don't|do not)\b", re.I)


def says_they_sell(summary: str) -> bool:
    """True if the summary claims a sale without any negation nearby (the 'we do NOT sell' trap)."""
    return any(SELL.search(s) and not NEG.search(s) for s in re.split(r"[.;]", summary))


def score(receipt: dict, case: dict) -> dict:
    items = {d["category"]: d for d in receipt["disclosures"]}
    status_hits = sum(items[c]["status"] == want for c, want in case["expected"].items())
    s = receipt["stats"]
    out = {"status_accuracy": status_hits / 5,
           "citation_validity": (s["quotes_verified"] / s["quotes_checked"]) if s["quotes_checked"] else 1.0,
           "negation_ok": None}
    if case["no_sale_claim"]:
        out["negation_ok"] = not says_they_sell(items["data_sharing"]["summary"])
    return out


def main() -> int:
    cfg = json.loads((ROOT / "cases.json").read_text())
    rows = []
    for case in cfg["cases"]:
        text = (ROOT / "policies" / case["file"]).read_text().strip()
        t0 = time.time()
        try:
            analysis, used = analyze_policy(text)
            r = build_receipt(text, analysis, used)
        except Exception as e:
            print(f"{case['name']}: FAILED ({e})"); continue
        res = score(r, case) | {"name": case["name"], "seconds": round(time.time() - t0, 1)}
        rows.append(res); time.sleep(5)
    if not rows:
        return 1
    print(f"\n{'case':<11}{'status acc':>11}{'citations':>11}{'negation':>10}{'secs':>7}")
    for r in rows:
        neg = "n/a" if r["negation_ok"] is None else ("pass" if r["negation_ok"] else "FAIL")
        print(f"{r['name']:<11}{r['status_accuracy']:>10.0%}{r['citation_validity']:>11.0%}{neg:>10}{r['seconds']:>7}")
    avg = lambda k: sum(r[k] for r in rows) / len(rows)
    print(f"{'average':<11}{avg('status_accuracy'):>10.0%}{avg('citation_validity'):>11.0%}")
    (ROOT / "results.json").write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
