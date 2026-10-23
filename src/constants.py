"""Shared constants. Pure Python, no third-party imports."""

CATEGORY_ORDER = [
    "data_collection",
    "data_usage",
    "data_sharing",
    "user_rights",
    "data_retention",
]

# "tag" is the small number that links a finding to its highlighted passage
# in the source view. The five categories are a fixed set, not a sequence.
CATEGORIES = {
    "data_collection": {
        "tag": 1,
        "title": "Data collected",
        "question": "What personal information is collected?",
    },
    "data_usage": {
        "tag": 2,
        "title": "How data is used",
        "question": "Why does the company collect it?",
    },
    "data_sharing": {
        "tag": 3,
        "title": "Third-party sharing",
        "question": "Who can receive the information?",
    },
    "user_rights": {
        "tag": 4,
        "title": "Your privacy rights",
        "question": "Can you access, delete, or control your data?",
    },
    "data_retention": {
        "tag": 5,
        "title": "Data retention",
        "question": "How long is the information kept?",
    },
}

# Final statuses shown to the user. The model only returns the first three;
# "verification_failed" is assigned by our own evidence check.
STATUS = {
    "disclosed": {"label": "Disclosed", "icon": "\u2713"},
    "unclear": {"label": "Unclear", "icon": "?"},
    "not_found": {"label": "Not found", "icon": "\u2013"},
    "verification_failed": {"label": "Verification failed", "icon": "\u2715"},
}

NOTICE = (
    "This receipt records what an automated analysis found in the text that was "
    "pasted. It is not legal advice, not a legal certification, and not a record "
    "that anyone consented to anything. A quote that was found proves the words "
    "are in the policy. It does not prove the plain-English summary reads them "
    "correctly."
)
