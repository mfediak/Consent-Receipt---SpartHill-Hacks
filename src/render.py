"""HTML and CSS for the ConsentReceipt interface.

Pure Python (no Streamlit import) so it can be unit tested. Every piece of text
that comes from the model or the pasted policy goes through esc() first.

Design notes
- Serif type is the policy's own words. Sans type is the plain-English reading.
  The reader can tell what was quoted and what was interpreted at a glance.
- The yellow highlighter is the only decorative color. It appears wherever a
  quote was found in the policy, and nowhere else.
- Status colors only appear on small labels, and every label also carries an
  icon and a word, so color is never the only signal.
"""

from __future__ import annotations

import html
from datetime import datetime

from .constants import NOTICE, STATUS

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap');

:root{
  --cr-page:#F3F5F9; --cr-sheet:#FFFFFF; --cr-ink:#1B2740; --cr-muted:#56627A;
  --cr-rule:#D3DAE6; --cr-rule-strong:#97A3BA; --cr-mark:#FFE45C;
  --cr-ok:#14633F; --cr-ok-bg:#E1F2E8;
  --cr-warn:#8F4B00; --cr-warn-bg:#FCE7CF;
  --cr-none:#3F4E66; --cr-none-bg:#E4E9F1;
  --cr-bad:#A11A1A; --cr-bad-bg:#FADDDD;
  --cr-sans:'Atkinson Hyperlegible',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --cr-serif:'Source Serif 4',Georgia,'Times New Roman',serif;
}

/* Streamlit chrome */
.stApp{background:var(--cr-page);color:var(--cr-ink);}
.stApp,.stApp p,.stApp label,.stApp textarea,.stApp input,.stApp button,
.stApp [data-testid="stMarkdownContainer"]{font-family:var(--cr-sans);}
.stApp [data-testid="stHeader"]{background:transparent;}
.stApp [data-testid="stToolbar"],.stApp [data-testid="stDecoration"],
.stApp #MainMenu,.stApp footer{display:none;}
.stApp .block-container{max-width:1080px;padding-top:1.6rem;padding-bottom:4rem;}
.stApp [data-testid="stSidebar"]{background:#E8ECF3;}
.stApp textarea{font-family:var(--cr-serif);font-size:1.05rem;line-height:1.6;color:var(--cr-ink);}
.stApp [data-baseweb="textarea"]:focus-within,
.stApp [data-baseweb="input"]:focus-within{box-shadow:0 0 0 3px var(--cr-mark);}
.stApp button:focus-visible,.stApp [role="tab"]:focus-visible{outline:3px solid var(--cr-ink);outline-offset:2px;}

/* Top bar and hero */
.cr .cr-bar{display:flex;align-items:center;padding:.2rem 0 1rem;margin:0 0 1.8rem;border-bottom:1px solid var(--cr-rule);}
.cr .cr-wordmark{font-weight:700;font-size:1.15rem;}
.cr .cr-wordmark mark{background:var(--cr-mark);color:var(--cr-ink);padding:.1em .45em;border-radius:2px;}
.cr .cr-hero{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:2rem 3rem;align-items:center;margin:0 0 2.4rem;}
.cr .cr-h1{font-size:clamp(2rem,4.4vw,3.1rem);font-weight:700;line-height:1.08;letter-spacing:-.015em;margin:0 0 1rem;max-width:16em;}
.cr .cr-lede{font-size:1.15rem;line-height:1.55;color:var(--cr-muted);max-width:34em;margin:0;}
.cr .cr-example{background:var(--cr-sheet);border:1px solid var(--cr-rule);border-top:4px solid var(--cr-ink);padding:1.3rem 1.5rem;}
.cr .cr-example-label{color:var(--cr-muted);font-size:.9rem;margin:0 0 .7rem;}
.cr .cr-h2{font-size:1.5rem;font-weight:700;line-height:1.2;margin:0 0 .3rem;}
.cr .cr-h3{font-size:1.1rem;font-weight:700;margin:0 0 .6rem;}
.cr .cr-help{color:var(--cr-muted);margin:0 0 1rem;line-height:1.5;}

/* Receipt sheet */
.cr .cr-sheet{background:var(--cr-sheet);border:1px solid var(--cr-rule);border-top:4px solid var(--cr-ink);margin:1rem 0 2rem;}
.cr .cr-sheet-head{display:flex;flex-wrap:wrap;gap:1rem 2rem;justify-content:space-between;align-items:flex-end;padding:1.6rem 1.8rem 1.3rem;border-bottom:2px dashed var(--cr-rule-strong);}
.cr .cr-company{color:var(--cr-muted);margin:.25rem 0 0;}
.cr .cr-facts{display:flex;flex-wrap:wrap;gap:.6rem 1.8rem;margin:0;}
.cr .cr-facts dt{font-size:.82rem;color:var(--cr-muted);margin:0;}
.cr .cr-facts dd{margin:0;font-weight:700;font-variant-numeric:tabular-nums;}
.cr .cr-hash{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9rem;}
.cr .cr-tally{display:flex;flex-wrap:wrap;gap:.5rem .6rem;align-items:center;padding:1rem 1.8rem;border-bottom:1px solid var(--cr-rule);}
.cr .cr-tally-note{flex-basis:100%;margin:.3rem 0 0;color:var(--cr-muted);font-size:.95rem;line-height:1.5;}

.cr .cr-badge{display:inline-flex;gap:.4rem;align-items:center;padding:.2rem .7rem;border-radius:999px;font-weight:700;font-size:.92rem;white-space:nowrap;}
.cr .cr-b-disclosed{background:var(--cr-ok-bg);color:var(--cr-ok);}
.cr .cr-b-unclear{background:var(--cr-warn-bg);color:var(--cr-warn);}
.cr .cr-b-not_found{background:var(--cr-none-bg);color:var(--cr-none);}
.cr .cr-b-verification_failed{background:var(--cr-bad-bg);color:var(--cr-bad);}

.cr .cr-row{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:1rem 2.2rem;padding:1.6rem 1.8rem;border-bottom:1px solid var(--cr-rule);}
.cr .cr-row-title{display:flex;gap:.65rem;align-items:center;font-weight:700;font-size:1.08rem;line-height:1.25;}
.cr .cr-tag{display:inline-grid;place-items:center;flex:none;width:1.65rem;height:1.65rem;border:2px solid var(--cr-ink);border-radius:50%;font-size:.82rem;font-weight:700;}
.cr .cr-row-q{color:var(--cr-muted);margin:.4rem 0 .9rem;font-size:.95rem;line-height:1.4;}
.cr .cr-summary{font-size:1.2rem;line-height:1.45;margin:0 0 1rem;max-width:34em;}
.cr .cr-summary-unverified{color:var(--cr-muted);}
.cr .cr-quote{margin:0 0 .75rem;padding:0 0 0 1rem;border:0;border-left:3px solid var(--cr-ink);font-family:var(--cr-serif);font-size:1.05rem;line-height:1.7;max-width:36em;}
.cr .cr-quote-unverified{border-left:3px dashed var(--cr-rule-strong);color:var(--cr-muted);}
.cr mark{background:var(--cr-mark);color:var(--cr-ink);padding:.06em .2em;border-radius:2px;-webkit-box-decoration-break:clone;box-decoration-break:clone;}
.cr .cr-verify{display:flex;gap:.5rem;align-items:baseline;font-size:.95rem;line-height:1.4;}
.cr .cr-v-ok{color:var(--cr-ok);} .cr .cr-v-bad{color:var(--cr-bad);} .cr .cr-v-none{color:var(--cr-none);}

.cr .cr-open{padding:1.5rem 1.8rem;background:#FBFCFE;border-bottom:1px solid var(--cr-rule);}
.cr .cr-open ul{margin:0;padding-left:1.2rem;}
.cr .cr-open li{margin:.4rem 0;line-height:1.5;max-width:44em;}
.cr .cr-notice{margin:0;padding:1.2rem 1.8rem 1.5rem;border-top:2px dashed var(--cr-rule-strong);color:var(--cr-muted);font-size:.92rem;line-height:1.55;}

/* Source view */
.cr .cr-legend{display:flex;flex-wrap:wrap;gap:.5rem 1.4rem;list-style:none;margin:0 0 1rem;padding:0;}
.cr .cr-legend li{display:flex;gap:.45rem;align-items:center;}
.cr .cr-policy{background:var(--cr-sheet);border:1px solid var(--cr-rule);padding:1.5rem 1.6rem .5rem;}
.cr .cr-para{display:grid;grid-template-columns:2.4rem minmax(0,1fr);gap:.4rem 1rem;margin:0 0 1.2rem;}
.cr .cr-pid{color:var(--cr-muted);font-size:.85rem;padding-top:.45rem;font-variant-numeric:tabular-nums;}
.cr .cr-para-text{margin:0;font-family:var(--cr-serif);font-size:1.05rem;line-height:1.75;max-width:40em;}
.cr .cr-pin{display:inline-grid;place-items:center;min-width:1.2rem;height:1.2rem;margin-left:.3rem;border-radius:50%;background:var(--cr-ink);color:#fff;font:700 .7rem var(--cr-sans);position:relative;top:-.4em;}
.cr .cr-legend .cr-pin{top:0;margin-left:0;}

@media (max-width:820px){
  .cr .cr-hero{grid-template-columns:1fr;}
  .cr .cr-row{grid-template-columns:1fr;padding:1.4rem 1.2rem;}
  .cr .cr-sheet-head,.cr .cr-tally,.cr .cr-open,.cr .cr-notice{padding-left:1.2rem;padding-right:1.2rem;}
}
"""


# --- helpers -----------------------------------------------------------------

def esc(value) -> str:
    """Escape text for HTML and flatten whitespace.

    Also escapes "$": Streamlit's markdown would otherwise treat dollar signs as math.
    """
    text = " ".join(str(value if value is not None else "").split())
    return html.escape(text, quote=True).replace("$", "&#36;")


def _esc_keep_breaks(value: str) -> str:
    return html.escape(value, quote=True).replace("$", "&#36;").replace("\n", "<br>")


def _flat(markup: str) -> str:
    """One line, no blank lines.

    Streamlit's markdown ends an HTML block at a blank line and turns lines
    indented by four spaces into code, so the markup is collapsed to one line.
    """
    return "".join(line.strip() for line in markup.splitlines())


def _badge(status: str) -> str:
    info = STATUS[status]
    return (
        f'<span class="cr-badge cr-b-{status}">'
        f'<span aria-hidden="true">{info["icon"]}</span>{esc(info["label"])}</span>'
    )


# --- top bar, hero -----------------------------------------------------------

def topbar_html() -> str:
    return _flat(
        """
        <div class="cr"><div class="cr-bar">
        <span class="cr-wordmark"><mark>ConsentReceipt</mark></span>
        </div></div>
        """
    )


def hero_html() -> str:
    return _flat(
        """
        <div class="cr"><div class="cr-hero">
        <div>
        <div role="heading" aria-level="1" class="cr-h1">Know what you’re agreeing to before you agree.</div>
        <p class="cr-lede">Paste a privacy policy. You get five plain-English findings, each tied to the exact words it came from, plus a plain list of what the policy leaves unsaid.</p>
        </div>
        <aside class="cr-example" aria-label="Example finding">
        <p class="cr-example-label">Example finding</p>
        <p class="cr-summary">Some of your information may be shared with advertising partners.</p>
        <blockquote class="cr-quote"><mark>We may share certain information with advertising partners.</mark></blockquote>
        <div class="cr-verify cr-v-ok"><span aria-hidden="true">✓</span><span>Exact match found in paragraph 4.</span></div>
        </aside>
        </div></div>
        """
    )


def section_title_html(title: str, help_text: str = "") -> str:
    help_html = f'<p class="cr-help">{esc(help_text)}</p>' if help_text else ""
    return _flat(
        f'<div class="cr"><div role="heading" aria-level="2" class="cr-h2">{esc(title)}</div>{help_html}</div>'
    )


# --- receipt sheet -----------------------------------------------------------

def _verify_line(f: dict) -> str:
    if f["evidence_verified"] is True:
        where = f"paragraph {f['paragraph_id'][1:]}" if f.get("paragraph_id") else "the policy"
        if f["match_type"] == "exact":
            text = f"Exact match found in {where}."
        else:
            text = f"Match found in {where}, once line breaks and quote marks are ignored."
        return f'<div class="cr-verify cr-v-ok"><span aria-hidden="true">✓</span><span>{esc(text)}</span></div>'
    if f["evidence_verified"] is False:
        return (
            '<div class="cr-verify cr-v-bad"><span aria-hidden="true">✕</span>'
            f'<span>{esc(f["note"])}</span></div>'
        )
    return (
        '<div class="cr-verify cr-v-none"><span aria-hidden="true">–</span>'
        f'<span>{esc(f["note"])}</span></div>'
    )


def finding_html(f: dict) -> str:
    unverified = f["status"] == "verification_failed"
    summary_cls = "cr-summary cr-summary-unverified" if unverified else "cr-summary"
    quote_html = ""
    if f["evidence"]:
        if f["evidence_verified"]:
            quote_html = f'<blockquote class="cr-quote"><mark>{esc(f["evidence"])}</mark></blockquote>'
        else:
            quote_html = (
                '<blockquote class="cr-quote cr-quote-unverified">'
                f'{esc(f["evidence"])}</blockquote>'
            )
    summary = esc(f["summary"]) or "No summary."
    if unverified:
        summary = f"Unverified: {summary}"
    return _flat(
        f"""
        <article class="cr-row">
        <div>
        <div class="cr-row-title"><span class="cr-tag">{f["tag"]}</span><span>{esc(f["title"])}</span></div>
        <p class="cr-row-q">{esc(f["question"])}</p>
        {_badge(f["status"])}
        </div>
        <div>
        <p class="{summary_cls}">{summary}</p>
        {quote_html}
        {_verify_line(f)}
        </div>
        </article>
        """
    )


def _tally_html(receipt: dict) -> str:
    s = receipt["summary"]
    chips = "".join(
        f'<span class="cr-badge cr-b-{key}"><span aria-hidden="true">{STATUS[key]["icon"]}</span>'
        f'{s[key]} {esc(STATUS[key]["label"].lower())}</span>'
        for key in STATUS
        if s[key]
    )
    checked, verified = s["quotes_checked"], s["quotes_verified"]
    if checked == 0:
        note = "There were no quotes to check, because the policy did not address any of the five questions."
    elif checked == verified:
        note = f"{verified} of {checked} quotes were found in the policy text."
    else:
        note = (
            f"{verified} of {checked} quotes were found in the policy text. "
            "The rest could not be located, so their summaries are marked unverified."
        )
    note += " A found quote shows the words are in the policy. Read it to confirm the summary matches."
    return f'<div class="cr-tally">{chips}<p class="cr-tally-note">{esc(note)}</p></div>'


def _open_questions_html(findings: list[dict]) -> str:
    items = []
    for f in findings:
        if f["status"] == "unclear":
            items.append(f"<li><strong>{esc(f['title'])}.</strong> {esc(f['summary'])}</li>")
        elif f["status"] == "not_found":
            items.append(f"<li><strong>{esc(f['title'])}.</strong> {esc(f['summary'])}</li>")
        elif f["status"] == "verification_failed":
            items.append(
                f"<li><strong>{esc(f['title'])}.</strong> This could not be confirmed against the policy. "
                "Check the policy yourself.</li>"
            )
    if items:
        body = f"<ul>{''.join(items)}</ul>"
    else:
        body = "<p class=\"cr-help\">Nothing flagged. Every category points to a passage that was found in the policy.</p>"
    return f'<section class="cr-open"><div role="heading" aria-level="3" class="cr-h3">What the policy leaves unclear</div>{body}</section>'


def _format_when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %Y, %H:%M UTC")
    except ValueError:
        return iso


def sheet_html(receipt: dict, findings: list[dict]) -> str:
    company = receipt["company"] or "Pasted policy"
    facts = [
        ("Analyzed", _format_when(receipt["analyzed_at"]), ""),
        ("Model", receipt["model"], ""),
        ("Policy fingerprint", receipt["policy_sha256"][:12], " cr-hash"),
        ("Time taken", f"{receipt['processing_seconds']} s", ""),
    ]
    facts_html = "".join(
        f'<div><dt>{esc(k)}</dt><dd class="{cls.strip()}">{esc(v)}</dd></div>' for k, v, cls in facts
    )
    rows = "".join(finding_html(f) for f in findings)
    return _flat(
        f"""
        <div class="cr"><section class="cr-sheet" aria-label="Privacy disclosure receipt">
        <header class="cr-sheet-head">
        <div>
        <div role="heading" aria-level="2" class="cr-h2">Privacy disclosure receipt</div>
        <p class="cr-company">{esc(company)}</p>
        </div>
        <dl class="cr-facts">{facts_html}</dl>
        </header>
        {_tally_html(receipt)}
        {rows}
        {_open_questions_html(findings)}
        <p class="cr-notice">{esc(NOTICE)}</p>
        </section></div>
        """
    )


# --- source view -------------------------------------------------------------

def legend_html(findings: list[dict]) -> str:
    found = [f for f in findings if f["evidence_verified"] is True]
    if not found:
        return '<div class="cr"><p class="cr-help">No quotes were located in the policy text, so nothing is highlighted.</p></div>'
    items = "".join(
        f'<li><span class="cr-pin">{f["tag"]}</span><span>{esc(f["title"])}</span></li>' for f in found
    )
    return f'<div class="cr"><ul class="cr-legend" aria-label="Highlight key">{items}</ul></div>'


def policy_html(text: str, paragraphs: list[dict], findings: list[dict]) -> str:
    """The pasted policy, labeled by paragraph, with each found quote highlighted.

    Overlapping quotes are handled by cutting the text at every quote boundary
    and tagging each piece with every quote that covers it.
    """
    spans = [
        (f["start"], f["end"], f["tag"])
        for f in findings
        if f["evidence_verified"] is True and f["start"] is not None
    ]
    cuts = sorted({0, len(text), *(s for s, _, _ in spans), *(e for _, e, _ in spans)})
    segments = list(zip(cuts, cuts[1:]))

    blocks = []
    for number, p in enumerate(paragraphs, start=1):
        parts = []
        for a, b in segments:
            lo, hi = max(a, p["start"]), min(b, p["end"])
            if lo >= hi:
                continue
            chunk = _esc_keep_breaks(text[lo:hi])
            covering = {t for s, e, t in spans if s <= a and b <= e}
            if covering:
                # Pin each quote's number once, at the end of its last piece.
                ending = sorted({t for s, e, t in spans if e == b and t in covering})
                pins = "".join(f'<span class="cr-pin">{t}</span>' for t in ending) if hi == b else ""
                parts.append(f"<mark>{chunk}{pins}</mark>")
            else:
                parts.append(chunk)
        blocks.append(
            f'<div class="cr-para"><span class="cr-pid">¶{number}</span>'
            f'<p class="cr-para-text">{"".join(parts)}</p></div>'
        )
    return f'<div class="cr"><div class="cr-policy">{"".join(blocks)}</div></div>'
