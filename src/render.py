"""HTML and CSS for the ConsentReceipt interface.

Pure Python (no Streamlit import) so it can be unit tested. Every piece of text
that comes from the model or the pasted policy goes through esc() first.

Design notes
- Direction: "Liquid Glass". An iridescent violet, pink and cyan backdrop, one
  large sheet of frosted glass for the working area, and a poster-style
  logotype (script over thin capitals) with glowing white type.
- Reading text never sits on the gradient. Body copy is dark ink on frosted
  white glass, and the glowing white type is confined to the hero poster,
  where the gradient is controlled.
- Serif type is the policy's own words. Sans type is the plain-English reading.
  A found quote gets a cyan-to-lilac marker and a numbered pin.
- Status colors only appear on small labels, and every label also carries an
  icon and a word, so color is never the only signal.
"""

from __future__ import annotations

import html
from datetime import datetime

from .constants import NOTICE, STATUS

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Pinyon+Script&family=Raleway:wght@300;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap');

:root{
  --cr-ink:#1E1B4B; --cr-muted:#4A4F78;
  --cr-violet:#4B3FC4; --cr-violet-soft:#6D5BF0; --cr-pink:#F27BC3; --cr-cyan:#8FE3F0; --cr-lilac:#C9B3FF;
  --cr-glass:rgba(255,255,255,.64); --cr-glass-strong:rgba(255,255,255,.82); --cr-edge:rgba(255,255,255,.92);
  --cr-line:rgba(30,27,75,.14); --cr-shadow:0 18px 50px rgba(76,52,170,.24);
  --cr-ok:#0F5C3A; --cr-ok-bg:#D8F3E4;
  --cr-warn:#8A4700; --cr-warn-bg:#FFE6C8;
  --cr-none:#3A4468; --cr-none-bg:#E2E6F4;
  --cr-bad:#9F1717; --cr-bad-bg:#FFDADA;
  --cr-sans:'Atkinson Hyperlegible',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --cr-serif:'Source Serif 4',Georgia,'Times New Roman',serif;
  --cr-script:'Pinyon Script','Snell Roundhand','Apple Chancery',cursive;
  --cr-display:Raleway,'Century Gothic','Avenir Next',system-ui,sans-serif;
}

/* Page: iridescent backdrop with a few glass orbs */
.stApp{
  background:
    radial-gradient(circle 190px at 83% 27%,rgba(255,255,255,.5),rgba(255,255,255,.12) 55%,transparent 58%),
    radial-gradient(circle 120px at 8% 64%,rgba(255,255,255,.42),rgba(255,255,255,.1) 55%,transparent 58%),
    radial-gradient(55% 45% at 6% 6%,#8E8CFF,transparent 70%),
    radial-gradient(50% 45% at 96% 4%,#8FE3F0,transparent 70%),
    radial-gradient(60% 55% at 4% 100%,#F2827F,transparent 70%),
    radial-gradient(55% 55% at 100% 96%,#D6A8FF,transparent 70%),
    #B49CF4;
  background-attachment:fixed;
  color:var(--cr-ink);
}
.stApp [data-testid="stAppViewContainer"],.stApp [data-testid="stMain"]{background:transparent;}
.stApp,.stApp p,.stApp label,.stApp textarea,.stApp input,.stApp button,
.stApp [data-testid="stMarkdownContainer"]{font-family:var(--cr-sans);}
.stApp [data-testid="stHeader"]{background:transparent;}
.stApp [data-testid="stToolbar"],.stApp [data-testid="stDecoration"],
.stApp #MainMenu,.stApp footer{display:none;}

/* The whole working area is one sheet of frosted glass */
.stApp .block-container{
  max-width:1120px;margin:1.4rem auto 3rem;padding:2.2rem 2.4rem 2.6rem;
  background:var(--cr-glass);
  -webkit-backdrop-filter:blur(26px) saturate(150%);backdrop-filter:blur(26px) saturate(150%);
  border:1px solid var(--cr-edge);border-radius:36px;
  box-shadow:var(--cr-shadow),inset 0 1px 0 #fff;
}
.stApp [data-testid="stSidebar"]{
  background:rgba(255,255,255,.6);
  -webkit-backdrop-filter:blur(24px) saturate(150%);backdrop-filter:blur(24px) saturate(150%);
  border-right:1px solid var(--cr-edge);
}
.stApp [data-testid="stSidebar"]>div{background:transparent;}
@supports not ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){
  .stApp .block-container,.stApp [data-testid="stSidebar"]{background:rgba(255,255,255,.92);}
}

/* Streamlit widgets, restyled */
.stApp [data-testid="stCaptionContainer"]{color:var(--cr-muted);}
.stApp textarea{font-family:var(--cr-serif);font-size:1.05rem;line-height:1.6;color:var(--cr-ink);}
.stApp [data-baseweb="textarea"],.stApp [data-baseweb="input"]{
  background:rgba(255,255,255,.78);border:1px solid var(--cr-edge);border-radius:18px;
  box-shadow:0 4px 18px rgba(76,52,170,.10);
}
.stApp [data-baseweb="base-input"],.stApp [data-baseweb="textarea"] textarea,
.stApp [data-baseweb="input"] input{background:transparent !important;color:var(--cr-ink);}
.stApp [data-baseweb="textarea"]:focus-within,.stApp [data-baseweb="input"]:focus-within{
  border-color:var(--cr-violet-soft);box-shadow:0 0 0 3px rgba(109,91,240,.35);
}
.stApp button[data-testid="stBaseButton-primary"],.stApp button[kind="primary"]{
  background:linear-gradient(135deg,#4B3FC4,#9B3AAE);color:#fff;border:1px solid rgba(255,255,255,.55);
  border-radius:999px;padding:.55rem 1.7rem;font-weight:700;
  box-shadow:0 10px 26px rgba(75,63,196,.35),inset 0 1px 0 rgba(255,255,255,.35);
  transition:filter .15s ease;
}
.stApp button[data-testid="stBaseButton-primary"]:hover,.stApp button[kind="primary"]:hover{filter:brightness(1.08);color:#fff;}
.stApp button[data-testid="stBaseButton-secondary"],.stApp button[kind="secondary"]{
  background:rgba(255,255,255,.72);color:var(--cr-ink);border:1px solid var(--cr-edge);border-radius:999px;
  box-shadow:0 4px 14px rgba(76,52,170,.10);
}
.stApp button[data-testid="stBaseButton-secondary"]:hover,.stApp button[kind="secondary"]:hover{
  background:#fff;color:var(--cr-ink);border-color:var(--cr-violet-soft);
}
.stApp button:focus-visible,.stApp [role="tab"]:focus-visible{outline:3px solid var(--cr-violet);outline-offset:2px;}
.stApp [data-baseweb="tab-highlight"]{background:linear-gradient(90deg,#6D5BF0,#F27BC3);height:3px;}
.stApp [data-testid="stExpander"]{background:rgba(255,255,255,.6);border:1px solid var(--cr-edge);border-radius:18px;}
.stApp [data-testid="stAlert"]{border-radius:18px;}

/* Top pill (results view) */
.cr .cr-pill{display:inline-flex;align-items:baseline;gap:.55rem;padding:.3rem 1.3rem .4rem;margin:0 0 1.4rem;
  background:var(--cr-glass-strong);border:1px solid var(--cr-edge);border-radius:999px;
  box-shadow:0 6px 20px rgba(76,52,170,.14),inset 0 1px 0 #fff;}
.cr .cr-script-sm{font-family:var(--cr-script);font-size:1.7rem;line-height:1;color:var(--cr-violet);}
.cr .cr-caps-sm{font-family:var(--cr-display);font-weight:600;font-size:.95rem;letter-spacing:.14em;text-transform:uppercase;}

/* Hero: the Liquid Glass poster */
.cr .cr-banner{position:relative;overflow:hidden;isolation:isolate;display:grid;place-items:center;
  min-height:19rem;padding:3.2rem 1.5rem;margin:0 0 2rem;border-radius:32px;
  background:
    radial-gradient(35% 60% at 100% 0%,rgba(143,227,240,.85),transparent 72%),
    radial-gradient(30% 50% at 0% 100%,rgba(255,160,140,.45),transparent 72%),
    linear-gradient(115deg,#6358EE 0%,#9A58DE 36%,#CF58A6 66%,#DD5C80 100%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.55),0 22px 50px rgba(90,60,200,.32);}
.cr .cr-banner::before,.cr .cr-banner::after{content:"";position:absolute;z-index:-1;border-radius:50%;
  border:1px solid rgba(255,255,255,.4);
  background:radial-gradient(circle at 30% 24%,rgba(255,255,255,.75),rgba(255,255,255,.14) 34%,rgba(255,255,255,.05) 70%);}
.cr .cr-banner::before{width:15rem;height:15rem;left:-3.5rem;bottom:-5.5rem;}
.cr .cr-banner::after{width:9rem;height:9rem;right:9%;top:-3rem;}
.cr .cr-star{position:absolute;width:1.9rem;height:1.9rem;fill:#fff;filter:drop-shadow(0 0 8px rgba(255,255,255,.95));}
.cr .cr-star-tl{left:1.1rem;top:1.1rem;} .cr .cr-star-tr{right:1.1rem;top:1.1rem;}
.cr .cr-star-bl{left:1.1rem;bottom:1.1rem;} .cr .cr-star-br{right:1.1rem;bottom:1.1rem;}
.cr .cr-logo{display:grid;justify-items:center;margin:0;}
.cr .cr-script{font-family:var(--cr-script);font-size:clamp(3.2rem,9vw,6.4rem);line-height:1;color:#fff;
  position:relative;z-index:1;margin-bottom:-.3em;
  text-shadow:0 0 22px rgba(255,255,255,.8),0 3px 26px rgba(60,30,140,.5);}
.cr .cr-caps{font-family:var(--cr-display);font-weight:300;font-size:clamp(3rem,12vw,8.6rem);line-height:1;
  letter-spacing:.05em;text-transform:uppercase;color:#fff;
  text-shadow:0 0 26px rgba(255,255,255,.7),0 4px 30px rgba(60,30,140,.5);}

.cr .cr-hero{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:1.6rem 2.6rem;align-items:center;margin:0 0 2.2rem;}
.cr .cr-promise{font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;line-height:1.15;letter-spacing:-.01em;margin:0 0 .9rem;max-width:15em;}
.cr .cr-lede{font-size:1.1rem;line-height:1.55;color:var(--cr-muted);max-width:34em;margin:0;}
.cr .cr-example{background:var(--cr-glass-strong);border:1px solid var(--cr-edge);border-radius:24px;padding:1.3rem 1.5rem;
  box-shadow:0 10px 30px rgba(76,52,170,.14),inset 0 1px 0 #fff;}
.cr .cr-example-label{color:var(--cr-muted);font-size:.9rem;margin:0 0 .7rem;}
.cr .cr-h2{font-size:1.5rem;font-weight:700;line-height:1.2;margin:0 0 .3rem;}
.cr .cr-h3{font-size:1.1rem;font-weight:700;margin:0 0 .6rem;}
.cr .cr-help{color:var(--cr-muted);margin:0 0 1rem;line-height:1.5;}

/* Receipt sheet */
.cr .cr-sheet{position:relative;overflow:hidden;background:var(--cr-glass-strong);border:1px solid var(--cr-edge);
  border-radius:28px;box-shadow:0 14px 40px rgba(76,52,170,.18),inset 0 1px 0 #fff;margin:1rem 0 2rem;}
.cr .cr-sheet::before{content:"";display:block;height:6px;background:linear-gradient(90deg,#8E8CFF,#F27BC3 40%,#F2827F 70%,#8FE3F0);}
.cr .cr-sheet-head{display:flex;flex-wrap:wrap;gap:1rem 2rem;justify-content:space-between;align-items:flex-end;
  padding:1.5rem 1.8rem 1.3rem;border-bottom:2px dashed rgba(30,27,75,.25);}
.cr .cr-company{color:var(--cr-muted);margin:.25rem 0 0;}
.cr .cr-facts{display:flex;flex-wrap:wrap;gap:.6rem 1.8rem;margin:0;}
.cr .cr-facts dt{font-size:.82rem;color:var(--cr-muted);margin:0;}
.cr .cr-facts dd{margin:0;font-weight:700;font-variant-numeric:tabular-nums;}
.cr .cr-hash{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9rem;}
.cr .cr-tally{display:flex;flex-wrap:wrap;gap:.5rem .6rem;align-items:center;padding:1rem 1.8rem;border-bottom:1px solid var(--cr-line);}
.cr .cr-tally-note{flex-basis:100%;margin:.3rem 0 0;color:var(--cr-muted);font-size:.95rem;line-height:1.5;}

.cr .cr-badge{display:inline-flex;gap:.4rem;align-items:center;padding:.2rem .75rem;border-radius:999px;
  font-weight:700;font-size:.92rem;white-space:nowrap;border:1px solid rgba(255,255,255,.9);}
.cr .cr-b-disclosed{background:var(--cr-ok-bg);color:var(--cr-ok);}
.cr .cr-b-unclear{background:var(--cr-warn-bg);color:var(--cr-warn);}
.cr .cr-b-not_found{background:var(--cr-none-bg);color:var(--cr-none);}
.cr .cr-b-verification_failed{background:var(--cr-bad-bg);color:var(--cr-bad);}

.cr .cr-row{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:1rem 2.2rem;padding:1.6rem 1.8rem;border-bottom:1px solid var(--cr-line);}
.cr .cr-row-title{display:flex;gap:.65rem;align-items:center;font-weight:700;font-size:1.08rem;line-height:1.25;}
.cr .cr-tag{display:inline-grid;place-items:center;flex:none;width:1.7rem;height:1.7rem;border:2px solid var(--cr-violet);
  color:var(--cr-violet);border-radius:50%;font-size:.82rem;font-weight:700;}
.cr .cr-row-q{color:var(--cr-muted);margin:.4rem 0 .9rem;font-size:.95rem;line-height:1.4;}
.cr .cr-summary{font-size:1.2rem;line-height:1.45;margin:0 0 1rem;max-width:34em;}
.cr .cr-summary-unverified{color:var(--cr-muted);}
.cr .cr-quote{margin:0 0 .8rem;padding:.7rem 1rem;background:rgba(255,255,255,.75);border:0;border-left:4px solid var(--cr-violet-soft);
  border-radius:0 14px 14px 0;font-family:var(--cr-serif);font-size:1.05rem;line-height:1.7;max-width:36em;}
.cr .cr-quote-unverified{border-left:4px dashed #8A8FB5;color:var(--cr-muted);background:rgba(255,255,255,.5);}
.cr mark{background:linear-gradient(100deg,rgba(143,227,240,.95),rgba(201,179,255,.95));color:var(--cr-ink);
  padding:.06em .22em;border-radius:6px;-webkit-box-decoration-break:clone;box-decoration-break:clone;}
.cr .cr-verify{display:flex;gap:.5rem;align-items:baseline;font-size:.95rem;line-height:1.4;}
.cr .cr-v-ok{color:var(--cr-ok);} .cr .cr-v-bad{color:var(--cr-bad);} .cr .cr-v-none{color:var(--cr-none);}

.cr .cr-open{padding:1.5rem 1.8rem;background:rgba(255,255,255,.45);border-bottom:1px solid var(--cr-line);}
.cr .cr-open ul{margin:0;padding-left:1.2rem;}
.cr .cr-open li{margin:.4rem 0;line-height:1.5;max-width:44em;}
.cr .cr-notice{margin:0;padding:1.2rem 1.8rem 1.5rem;border-top:2px dashed rgba(30,27,75,.25);color:var(--cr-muted);font-size:.92rem;line-height:1.55;}

/* Source view */
.cr .cr-legend{display:flex;flex-wrap:wrap;gap:.5rem 1.4rem;list-style:none;margin:0 0 1rem;padding:0;}
.cr .cr-legend li{display:flex;gap:.45rem;align-items:center;}
.cr .cr-policy{background:var(--cr-glass-strong);border:1px solid var(--cr-edge);border-radius:24px;padding:1.5rem 1.6rem .5rem;
  box-shadow:0 10px 30px rgba(76,52,170,.12),inset 0 1px 0 #fff;}
.cr .cr-para{display:grid;grid-template-columns:2.4rem minmax(0,1fr);gap:.4rem 1rem;margin:0 0 1.2rem;}
.cr .cr-pid{color:var(--cr-muted);font-size:.85rem;padding-top:.45rem;font-variant-numeric:tabular-nums;}
.cr .cr-para-text{margin:0;font-family:var(--cr-serif);font-size:1.05rem;line-height:1.75;max-width:40em;}
.cr .cr-pin{display:inline-grid;place-items:center;min-width:1.2rem;height:1.2rem;margin-left:.3rem;border-radius:50%;
  background:var(--cr-violet);color:#fff;font:700 .7rem var(--cr-sans);position:relative;top:-.4em;}
.cr .cr-legend .cr-pin{top:0;margin-left:0;}

@media (max-width:820px){
  .stApp .block-container{margin:.5rem;padding:1.1rem;border-radius:26px;}
  .cr .cr-banner{min-height:14rem;padding:2.4rem 1rem;border-radius:24px;}
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

_STAR = (
    '<svg class="cr-star cr-star-{pos}" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 0C12 7 17 12 24 12C17 12 12 17 12 24C12 17 7 12 0 12C7 12 12 7 12 0Z"/></svg>'
)


def topbar_html() -> str:
    """Compact brand pill for the results view."""
    return _flat(
        """
        <div class="cr"><div class="cr-pill" aria-label="ConsentReceipt">
        <span class="cr-script-sm" aria-hidden="true">Consent</span>
        <span class="cr-caps-sm" aria-hidden="true">Receipt</span>
        </div></div>
        """
    )


def hero_html() -> str:
    """Logotype poster, then the promise and one worked example."""
    stars = "".join(_STAR.format(pos=pos) for pos in ("tl", "tr", "bl", "br"))
    return _flat(
        f"""
        <div class="cr">
        <section class="cr-banner" aria-label="ConsentReceipt">
        {stars}
        <div role="heading" aria-level="1" aria-label="ConsentReceipt" class="cr-logo">
        <span class="cr-script" aria-hidden="true">Consent</span>
        <span class="cr-caps" aria-hidden="true">Receipt</span>
        </div>
        </section>
        <div class="cr-hero">
        <div>
        <p class="cr-promise">Know what you’re agreeing to before you agree.</p>
        <p class="cr-lede">Paste a privacy policy. You get five plain-English findings, each tied to the exact words it came from, plus a plain list of what the policy leaves unsaid.</p>
        </div>
        <aside class="cr-example" aria-label="Example finding">
        <p class="cr-example-label">Example finding</p>
        <p class="cr-summary">Some of your information may be shared with advertising partners.</p>
        <blockquote class="cr-quote"><mark>We may share certain information with advertising partners.</mark></blockquote>
        <div class="cr-verify cr-v-ok"><span aria-hidden="true">✓</span><span>Exact match found in paragraph 4.</span></div>
        </aside>
        </div>
        </div>
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
