from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from models.note import Note

_FONT_REGISTERED = False


def build_study_material_pdf(note: Note) -> bytes:
    _register_unicode_font()
    stream = BytesIO()
    document = SimpleDocTemplate(
        stream,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Study material: {note.title}",
        author="AI Study Assistant",
    )
    styles = getSampleStyleSheet()
    font_name = "StudyAssistant"
    title_style = ParagraphStyle(
        "StudyTitle",
        parent=styles["Title"],
        fontName=f"{font_name}-Bold",
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#30254f"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "StudyMeta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#77738a"),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "StudyHeading",
        parent=styles["Heading2"],
        fontName=f"{font_name}-Bold",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#7053d7"),
        spaceBefore=13,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "StudyBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor("#373548"),
        splitLongWords=True,
        spaceAfter=5,
    )
    story = [
        Paragraph(escape(note.title), title_style),
        Paragraph(
            escape(note.subject or "General study note")
            + " &nbsp; · &nbsp; AI-generated study material",
            meta_style,
        ),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e9e4f7")),
        Spacer(1, 13),
        Paragraph("3 Key Takeaways", heading_style),
        *_paragraphs(note.ai_summary, body_style),
        Spacer(1, 7),
        KeepTogether(
            [
                Paragraph("AI Confuser · Test Your Understanding", heading_style),
                *_paragraphs(note.ai_confuser, body_style),
            ]
        ),
        Spacer(1, 16),
        Paragraph(
            "Use this material as a learning aid and verify important ideas with your course resources.",
            meta_style,
        ),
    ]
    document.build(story)
    return stream.getvalue()


def _paragraphs(text: str, style: ParagraphStyle) -> list[Paragraph]:
    chunks = [chunk.strip() for chunk in text.splitlines() if chunk.strip()]
    if not chunks:
        return [Paragraph("No material available.", style)]
    return [
        Paragraph(escape(chunk).replace("\n", "<br/>"), style)
        for chunk in chunks
    ]


def _register_unicode_font() -> None:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    font_directory = Path(__file__).parent.parent / "static" / "fonts"
    regular_candidates = [
        font_directory / "DejaVuSans.ttf",
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    bold_candidates = [
        font_directory / "DejaVuSans-Bold.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
    ]
    regular_path = next((path for path in regular_candidates if path.is_file()), None)
    bold_path = next((path for path in bold_candidates if path.is_file()), None)
    if regular_path is None or bold_path is None:
        current_app.logger.error("Unicode font files are unavailable; cannot create study PDF.")
        raise RuntimeError("PDF font files are missing. Install DejaVu Sans or Arial fonts.")
    pdfmetrics.registerFont(TTFont("StudyAssistant", str(regular_path)))
    pdfmetrics.registerFont(TTFont("StudyAssistant-Bold", str(bold_path)))
    _FONT_REGISTERED = True
