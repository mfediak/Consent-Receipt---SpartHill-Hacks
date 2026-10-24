from io import BytesIO
from xml.sax.saxutils import escape

from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


class ReportDisclosure(BaseModel):
    category: str
    category_label: str | None = None
    summary: str
    evidence: str = ""
    status: str
    status_label: str | None = None
    evidence_verified: bool | None = None


class ReportStats(BaseModel):
    quotes_checked: int
    quotes_verified: int


class PolicyReport(BaseModel):
    company: str
    overview: str
    generated_at: str
    policy_sha256: str
    model: str
    disclosures: list[ReportDisclosure]
    stats: ReportStats
    disclaimer: str
    ui_labels: dict[str, str] = Field(default_factory=dict)


def _paragraph_text(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def build_report_pdf(report: PolicyReport) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=0.7 * inch, leftMargin=0.7 * inch,
        topMargin=0.65 * inch, bottomMargin=0.65 * inch,
        title=f"ConsentReceipt - {report.company}", author="ConsentReceipt",
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle("ReceiptTitle", parent=base["Title"], textColor=colors.HexColor("#25364A"),
                           alignment=TA_LEFT, spaceAfter=8)
    body = ParagraphStyle("ReceiptBody", parent=base["BodyText"], leading=15, spaceAfter=8)
    heading = ParagraphStyle("DisclosureHeading", parent=base["Heading2"], textColor=colors.HexColor("#176B67"),
                             spaceBefore=12, spaceAfter=5)
    quote = ParagraphStyle("EvidenceQuote", parent=body, leftIndent=12,
                           textColor=colors.HexColor("#46545D"), fontName="Helvetica-Oblique")
    labels = report.ui_labels
    story = [
        Paragraph("ConsentReceipt", title),
        Paragraph(_paragraph_text(report.company), base["Heading1"]),
        Paragraph(_paragraph_text(report.overview), body),
    ]
    metadata = [
        [_paragraph_text(labels.get("generated", "Generated")), _paragraph_text(report.generated_at)],
        [_paragraph_text(labels.get("quotesVerified", "Quotes verified")), f"{report.stats.quotes_verified} of {report.stats.quotes_checked}"],
        [_paragraph_text(labels.get("fingerprint", "Policy fingerprint")), _paragraph_text(report.policy_sha256)],
        [_paragraph_text(labels.get("analysisModel", "Analysis model")), _paragraph_text(report.model)],
    ]
    table = Table(metadata, colWidths=[1.35 * inch, 5.45 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#59666F")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([table, Spacer(1, 10)])

    for disclosure in report.disclosures:
        category_label = disclosure.category_label or disclosure.category.replace("_", " ").title()
        status_label = disclosure.status_label or disclosure.status.replace("_", " ").title()
        story.append(Paragraph(_paragraph_text(category_label), heading))
        story.append(Paragraph(f"<b>{_paragraph_text(status_label)}</b>  "
                               f"{_paragraph_text(disclosure.summary)}", body))
        if disclosure.evidence:
            verified = labels.get("quoteVerified", "Verified quote") if disclosure.evidence_verified else labels.get("quoteUnverified", "Quote not verified")
            story.append(Paragraph(f"<b>{verified}:</b> “{_paragraph_text(disclosure.evidence)}”", quote))
        else:
            story.append(Paragraph(_paragraph_text(labels.get("noQuote", "No supporting quote was found in the policy.")), quote))

    story.extend([Spacer(1, 18), Paragraph(_paragraph_text(labels.get("important", "Important")), heading), Paragraph(_paragraph_text(report.disclaimer), body)])
    document.build(story)
    return buffer.getvalue()