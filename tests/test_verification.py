from pathlib import Path

from src.constants import CATEGORY_ORDER
from src.receipt import build_receipt, receipt_to_json, receipt_to_text
from src.render import esc, finding_html, policy_html, sheet_html
from src.verification import (
    locate_evidence,
    normalize_policy,
    policy_fingerprint,
    split_paragraphs,
    verify_disclosures,
)

SAMPLES = Path(__file__).parent.parent / "samples"
POLICY = normalize_policy((SAMPLES / "sample_policy.txt").read_text(encoding="utf-8"))


def item(category, evidence, status="disclosed", summary="A summary."):
    return {"category": category, "evidence": evidence, "summary": summary, "status": status}


def by_cat(findings):
    return {f["category"]: f for f in findings}


# --- locating quotes ---------------------------------------------------------

def test_exact_quote_is_found_with_offsets():
    quote = "We may share certain information with advertising partners."
    hit = locate_evidence(POLICY, quote)
    assert hit["match_type"] == "exact"
    assert POLICY[hit["start"]:hit["end"]] == quote


def test_made_up_quote_is_rejected():
    assert locate_evidence(POLICY, "We never share your data with anyone at all.") is None


def test_line_breaks_and_curly_quotes_are_tolerated_but_words_must_match():
    text = "You can’t opt out of\nanalytics cookies on this site."
    hit = locate_evidence(text, "You can't opt out of analytics cookies on this site.")
    assert hit is not None and hit["match_type"] == "normalized"
    assert locate_evidence(text, "You can't opt out of advertising cookies on this site.") is None


def test_wrapping_quotation_marks_are_ignored():
    hit = locate_evidence(POLICY, '"We retain your information for as long as necessary to provide our services."')
    assert hit is not None


def test_too_short_quote_proves_nothing():
    assert locate_evidence(POLICY, "We use") is None


def test_ellipsis_quotes_fail():
    assert locate_evidence(POLICY, "We collect your name... and browsing activity.") is None


# --- final statuses ----------------------------------------------------------

def test_statuses_cover_all_four_outcomes():
    findings = by_cat(
        verify_disclosures(
            POLICY,
            [
                item("data_collection", "We collect your name, email address, device identifiers, and browsing activity."),
                item("data_retention", "We retain your information for as long as necessary to provide our services.", "unclear"),
                item("user_rights", "", "not_found"),
                item("data_sharing", "We sell everything to everyone, always.", "disclosed"),
            ],
        )
    )
    assert findings["data_collection"]["status"] == "disclosed"
    assert findings["data_collection"]["evidence_verified"] is True
    assert findings["data_retention"]["status"] == "unclear"
    assert findings["user_rights"]["status"] == "not_found"
    assert findings["user_rights"]["evidence_verified"] is None
    assert findings["data_sharing"]["status"] == "verification_failed"
    assert findings["data_sharing"]["evidence_verified"] is False


def test_always_five_findings_in_order_even_if_model_skips_one():
    findings = verify_disclosures(POLICY, [item("data_usage", "We use this information to provide services, personalize advertisements, and improve our products.")])
    assert [f["category"] for f in findings] == CATEGORY_ORDER
    assert by_cat(findings)["data_sharing"]["status"] == "verification_failed"


def test_disclosed_without_a_quote_fails_verification():
    findings = by_cat(verify_disclosures(POLICY, [item("data_usage", "", "disclosed")]))
    assert findings["data_usage"]["status"] == "verification_failed"


def test_not_found_ignores_any_quote_the_model_adds():
    findings = by_cat(verify_disclosures(POLICY, [item("user_rights", "We collect your name, email address.", "not_found")]))
    assert findings["user_rights"]["status"] == "not_found"
    assert findings["user_rights"]["evidence"] == ""


def test_negation_is_kept_in_the_quoted_evidence():
    text = (SAMPLES / "sample_negation.txt").read_text(encoding="utf-8")
    text = normalize_policy(text)
    findings = by_cat(verify_disclosures(text, [item("data_sharing", "We do not sell your personal information.")]))
    assert findings["data_sharing"]["evidence_verified"] is True
    assert "do not sell" in findings["data_sharing"]["evidence"]
    # A model that flips the meaning cannot pass by quoting the flipped sentence.
    flipped = by_cat(verify_disclosures(text, [item("data_sharing", "We sell your personal information.")]))
    assert flipped["data_sharing"]["status"] == "verification_failed"


# --- paragraphs --------------------------------------------------------------

def test_paragraph_labels_and_location():
    paragraphs = split_paragraphs(POLICY)
    assert [p["id"] for p in paragraphs] == ["P1", "P2", "P3", "P4"]
    findings = by_cat(verify_disclosures(POLICY, [item("data_sharing", "We may share certain information with advertising partners.")]))
    assert findings["data_sharing"]["paragraph_id"] == "P2"


def test_single_block_falls_back_to_line_splitting():
    assert len(split_paragraphs("one line here\nsecond line here")) == 2


# --- receipt -----------------------------------------------------------------

def make_receipt():
    findings = verify_disclosures(
        POLICY,
        [
            item("data_collection", "We collect your name, email address, device identifiers, and browsing activity."),
            item("data_retention", "We retain your information for as long as necessary to provide our services.", "unclear"),
            item("user_rights", "", "not_found"),
            item("data_sharing", "We sell everything to everyone, always.", "disclosed"),
        ],
    )
    receipt = build_receipt(company=" Example Co ", source="", policy_text=POLICY, findings=findings, model="test-model", elapsed_seconds=3.14159)
    return receipt, findings


def test_receipt_contents():
    receipt, _ = make_receipt()
    assert receipt["company"] == "Example Co"
    assert receipt["policy_source"] is None
    assert receipt["policy_sha256"] == policy_fingerprint(POLICY)
    assert receipt["processing_seconds"] == 3.1
    assert receipt["summary"]["quotes_checked"] == 3  # not_found expects no quote
    assert receipt["summary"]["quotes_verified"] == 2
    assert "not legal advice" in receipt["notice"]
    assert POLICY not in receipt_to_json(receipt)  # fingerprint only, never the full policy


def test_fingerprint_is_stable_for_same_text():
    assert policy_fingerprint(POLICY) == policy_fingerprint(normalize_policy(POLICY + "\n\n"))


def test_text_export_flags_unverified_quotes():
    receipt, _ = make_receipt()
    text = receipt_to_text(receipt)
    assert "NOT found in policy" in text
    assert "Data retention: Unclear" in text


# --- rendering ---------------------------------------------------------------

def test_model_text_is_escaped():
    assert esc('<script>alert("x")</script> $5') == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &#36;5"
    findings = verify_disclosures(POLICY, [item("data_usage", "<img src=x onerror=alert(1)> padding padding", "disclosed", "<b>bold</b>")])
    markup = finding_html(by_cat(findings)["data_usage"])
    assert "<img" not in markup and "<b>" not in markup


def test_markup_has_no_blank_lines_or_leading_indent():
    receipt, findings = make_receipt()
    markup = sheet_html(receipt, findings)
    assert "\n" not in markup


def test_policy_view_marks_found_quotes_and_pins_numbers():
    receipt, findings = make_receipt()
    markup = policy_html(POLICY, split_paragraphs(POLICY), findings)
    assert "<mark>We collect your name" in markup
    assert 'class="cr-pin">1<' in markup


def test_overlapping_quotes_both_get_pins():
    text = "We share data with partners and we keep logs for ninety days after you leave."
    findings = verify_disclosures(
        text,
        [
            item("data_sharing", "We share data with partners and we keep logs"),
            item("data_retention", "we keep logs for ninety days after you leave."),
        ],
    )
    markup = policy_html(text, split_paragraphs(text), findings)
    assert 'class="cr-pin">3<' in markup and 'class="cr-pin">5<' in markup
