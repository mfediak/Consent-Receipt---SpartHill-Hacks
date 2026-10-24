"""Test Groq on the sample policy.   Usage:  python -m scripts.check_providers"""
import time
from pathlib import Path
from app import analyzer as a

text = (Path(__file__).resolve().parent.parent / "samples" / "sample_policy.txt").read_text(encoding="utf-8").strip()
prompt = f"{a.RULES}\n\n<policy>\n{text}\n</policy>"
providers = a.active_providers()
if not providers:
    raise SystemExit("FAIL: GROQ_API_KEY is missing or still has the example placeholder. Add a real key to .env.")

print("Groq configured:", bool(providers))
failed = False
for p in providers:
    for m in a.models_for(p):
        t0 = time.time()
        try:
            out = a._parse(a._generate(p, m, prompt))
            print(f"  OK    {p}/{m}: {len(out.disclosures)} disclosures in {time.time() - t0:.1f}s")
        except Exception as e:
            failed = True
            print(f"  FAIL  {p}/{m}: {str(e)[:260]}")
if failed:
    raise SystemExit("\nGroq check failed. Verify the key and model in .env, then retry.")
print("\nGroq is reachable and the response was parsed successfully.")
