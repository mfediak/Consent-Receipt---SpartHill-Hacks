"""Evidence verification: the AI's quotes are never trusted, only checked."""
import re

# One-to-one character swaps keep string indices identical to the original text.
_TABLE = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u00a0": " "})
MIN_QUOTE_LEN = 12


def find_evidence(policy_text: str, evidence: str) -> tuple[int, int] | None:
    """Return (start, end) of the quote inside policy_text, or None if it isn't there.

    Matching ignores case, whitespace differences, and curly-vs-straight quotes,
    but every word must appear in the same order, contiguously.
    """
    quote = (evidence or "").translate(_TABLE).strip().strip("\"'")
    if len(quote) < MIN_QUOTE_LEN:
        return None
    pattern = r"\s+".join(re.escape(word) for word in quote.split())
    match = re.search(pattern, policy_text.translate(_TABLE), re.IGNORECASE)
    return (match.start(), match.end()) if match else None


def verify_evidence(policy_text: str, evidence: str) -> bool:
    return find_evidence(policy_text, evidence) is not None
