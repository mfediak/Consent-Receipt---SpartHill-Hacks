from app.verification import find_evidence, verify_evidence

POLICY = "We do not sell your personal information.  We may share data\nwith advertising partners. It\u2019s perfectly fine."


def test_exact_quote_found_with_correct_span():
    q = "We may share data with advertising partners"
    s, e = find_evidence(POLICY, q)
    assert " ".join(POLICY[s:e].split()) == q


def test_whitespace_case_and_curly_quotes_tolerated():
    assert verify_evidence(POLICY, "we MAY share data with advertising partners")
    assert verify_evidence(POLICY, "It's perfectly fine.")


def test_invented_quote_rejected():
    assert not verify_evidence(POLICY, "We sell your personal information to brokers")


def test_negation_cannot_be_dropped():
    assert not verify_evidence(POLICY, "We sell your personal information")


def test_empty_or_tiny_quotes_rejected():
    assert not verify_evidence(POLICY, "")
    assert not verify_evidence(POLICY, "We")


def test_reordered_words_rejected():
    assert not verify_evidence(POLICY, "advertising partners share data We may")


def test_negation_heuristic():
    from scripts.evaluate import says_they_sell
    assert not says_they_sell("They say they do not sell your data.")
    assert says_they_sell("The company sells your data to advertisers.")
