import io
import base64
import zipfile
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models.evaluation import Evaluation
from app.models.participant import Participant
from app.schemas.result import ExecutiveReportResults
from app.services.results_service import (
    calculate_evaluation_results,
    calculate_participant_results,
    calculate_executive_report_results,
)
from app.services.chart_service import (
    generate_competency_items_chart,
    generate_ranking_bars_chart,
    generate_scatter_plot,
    generate_segmented_scatter_plot,
)


def _get_pdf_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0176d3"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=TA_LEFT,
        spaceAfter=12,
    )

    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    body_bold = ParagraphStyle(
        "BodyTextBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    kpi_number_style = ParagraphStyle(
        "KpiNumber",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#0176d3"),
        alignment=TA_CENTER,
    )

    kpi_label_style = ParagraphStyle(
        "KpiLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
        alignment=TA_LEFT,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
    )

    table_cell_right = ParagraphStyle(
        "TableCellRight",
        parent=table_cell_style,
        alignment=TA_RIGHT,
    )

    badge_strength = ParagraphStyle(
        "BadgeStrength",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#16a34a"),
    )

    badge_opportunity = ParagraphStyle(
        "BadgeOpportunity",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#d97706"),
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h2": h2_style,
        "body": body_style,
        "body_bold": body_bold,
        "kpi_number": kpi_number_style,
        "kpi_label": kpi_label_style,
        "table_header": table_header_style,
        "table_cell": table_cell_style,
        "table_cell_bold": table_cell_bold,
        "table_cell_right": table_cell_right,
        "badge_strength": badge_strength,
        "badge_opportunity": badge_opportunity,
    }


def generate_general_results_pdf(db: Session, company_id: UUID, evaluation_id: UUID) -> bytes:
    evaluation = db.get(Evaluation, evaluation_id)
    eval_title = evaluation.title if evaluation else "Evaluación 360°"
    results = calculate_evaluation_results(db, company_id, evaluation_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    st = _get_pdf_styles()
    story = []

    # Title & Header
    story.append(Paragraph(f"Informe General 360° — {eval_title}", st["title"]))
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"RRHH 360 Platform • Generado el {date_str}", st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0176d3"), spaceAfter=14))

    # Summary KPI Cards
    kpi_data = [
        [
            Paragraph(f"{results.average:.2f} / 4.00", st["kpi_number"]),
            Paragraph(f"{results.median:.2f}", st["kpi_number"]),
            Paragraph(f"{results.stddev:.2f}", st["kpi_number"]),
            Paragraph(f"{len(results.ranking)}", st["kpi_number"]),
        ],
        [
            Paragraph("PROMEDIO GENERAL", st["kpi_label"]),
            Paragraph("MEDIANA", st["kpi_label"]),
            Paragraph("DESVIACIÓN ESTÁNDAR", st["kpi_label"]),
            Paragraph("EVALUADOS", st["kpi_label"]),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 130])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    # Competencies Breakdown
    story.append(Paragraph("Resumen por Competencias", st["h2"]))
    comp_headers = [
        Paragraph("Competencia", st["table_header"]),
        Paragraph("Promedio", st["table_header"]),
        Paragraph("Prom. Ponderado", st["table_header"]),
        Paragraph("Mediana", st["table_header"]),
        Paragraph("Desv. Est.", st["table_header"]),
        Paragraph("Respuestas", st["table_header"]),
    ]
    comp_rows = [comp_headers]

    for c in results.competencies:
        comp_rows.append(
            [
                Paragraph(c.competency_name, st["table_cell_bold"]),
                Paragraph(f"{c.average:.2f}", st["table_cell_right"]),
                Paragraph(f"{c.weighted_average:.2f}", st["table_cell_right"]),
                Paragraph(f"{c.median:.2f}", st["table_cell_right"]),
                Paragraph(f"{c.stddev:.2f}", st["table_cell_right"]),
                Paragraph(str(c.responses), st["table_cell_right"]),
            ]
        )

    comp_table = Table(comp_rows, colWidths=[190, 65, 75, 60, 65, 65])
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r_idx in range(1, len(comp_rows)):
        if r_idx % 2 == 0:
            t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f8fafc")))
    comp_table.setStyle(TableStyle(t_style))
    story.append(comp_table)
    story.append(Spacer(1, 16))

    # Participants Ranking Table
    story.append(Paragraph("Ranking General de Colaboradores", st["h2"]))
    rank_headers = [
        Paragraph("#", st["table_header"]),
        Paragraph("Colaborador", st["table_header"]),
        Paragraph("Promedio General", st["table_header"]),
    ]
    rank_rows = [rank_headers]

    for item in results.ranking:
        rank_rows.append(
            [
                Paragraph(str(item.rank), st["table_cell_bold"]),
                Paragraph(item.participant_name, st["table_cell"]),
                Paragraph(f"<b>{item.average:.2f}</b> / 4.00", st["table_cell_right"]),
            ]
        )

    rank_table = Table(rank_rows, colWidths=[40, 340, 140])
    r_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r_idx in range(1, len(rank_rows)):
        if r_idx % 2 == 0:
            r_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f8fafc")))
    rank_table.setStyle(TableStyle(r_style))
    story.append(rank_table)

    # Outlier alerts section if any
    if results.outliers:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Alertas de Sesgo / Outliers Detectados", st["h2"]))
        outlier_rows = [
            [
                Paragraph("Evaluador", st["table_header"]),
                Paragraph("Evaluado", st["table_header"]),
                Paragraph("Puntaje", st["table_header"]),
                Paragraph("Promedio Grupo", st["table_header"]),
                Paragraph("Detalle", st["table_header"]),
            ]
        ]
        for alert in results.outliers:
            msg_color = "#dc2626" if alert.alert_type == "low_outlier" else "#16a34a"
            msg_p = Paragraph(f"<font color='{msg_color}'>{alert.message}</font>", st["table_cell"])
            outlier_rows.append(
                [
                    Paragraph(alert.evaluator_name, st["table_cell"]),
                    Paragraph(alert.evaluatee_name, st["table_cell_bold"]),
                    Paragraph(f"{alert.evaluator_average:.2f}", st["table_cell_right"]),
                    Paragraph(f"{alert.others_average:.2f}", st["table_cell_right"]),
                    msg_p,
                ]
            )
        outlier_table = Table(outlier_rows, colWidths=[100, 100, 50, 80, 190])
        outlier_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(outlier_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_participant_results_pdf(
    db: Session, company_id: UUID, evaluation_id: UUID, participant_id: UUID
) -> bytes:
    evaluation = db.get(Evaluation, evaluation_id)
    participant = db.get(Participant, participant_id)
    p_results = calculate_participant_results(db, company_id, evaluation_id, participant_id)

    eval_title = evaluation.title if evaluation else "Evaluación 360°"
    p_name = participant.full_name if participant else p_results.participant_name
    p_role = participant.role if (participant and participant.role) else (p_results.participant_role or "Colaborador")
    p_email = participant.email if (participant and participant.email) else (p_results.participant_email or "")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    st = _get_pdf_styles()
    story = []

    # Title & Header
    story.append(Paragraph(f"Informe Individual 360° — {p_name}", st["title"]))
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(
        Paragraph(
            f"<b>Rol:</b> {p_role} &nbsp;|&nbsp; <b>Email:</b> {p_email} &nbsp;|&nbsp; <b>Evaluación:</b> {eval_title} ({date_str})",
            st["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0176d3"), spaceAfter=14))

    # KPI Summary Cards (Evaluadores, Autoevaluación, Brecha)
    eval_score_str = f"{p_results.overall_evaluators_score:.2f} / 4.00" if p_results.overall_evaluators_score is not None else "N/A"
    self_score_str = f"{p_results.overall_self_score:.2f} / 4.00" if p_results.overall_self_score is not None else "N/A"
    
    gap_str = "N/A"
    gap_color = "#334155"
    if p_results.overall_gap is not None:
        if p_results.overall_gap > 0:
            gap_str = f"+{p_results.overall_gap:.2f} (Sobrestimación)"
            gap_color = "#d97706"
        elif p_results.overall_gap < 0:
            gap_str = f"{p_results.overall_gap:.2f} (Subestimación)"
            gap_color = "#16a34a"
        else:
            gap_str = "0.00 (Alineado)"
            gap_color = "#16a34a"

    gap_style = ParagraphStyle(
        "GapNumber",
        parent=st["kpi_number"],
        textColor=colors.HexColor(gap_color),
        fontSize=13,
    )

    kpi_data = [
        [
            Paragraph(eval_score_str, st["kpi_number"]),
            Paragraph(self_score_str, st["kpi_number"]),
            Paragraph(gap_str, gap_style),
        ],
        [
            Paragraph("PROMEDIO EVALUADORES", st["kpi_label"]),
            Paragraph("AUTOEVALUACIÓN", st["kpi_label"]),
            Paragraph("BRECHA (AUTO vs EVALUADORES)", st["kpi_label"]),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[170, 170, 180])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # Top Strengths & Opportunities
    story.append(Paragraph("Puntos Destacados", st["h2"]))
    
    strengths_html = "<br/>".join([f"• {s}" for s in p_results.top_strengths]) if p_results.top_strengths else "No registradas"
    opps_html = "<br/>".join([f"• {o}" for o in p_results.opportunities]) if p_results.opportunities else "No registradas"

    highlights_data = [
        [
            Paragraph("<b>TOP FORTALEZAS</b>", st["badge_strength"]),
            Paragraph("<b>ÁREAS DE OPORTUNIDAD</b>", st["badge_opportunity"]),
        ],
        [
            Paragraph(strengths_html, st["table_cell"]),
            Paragraph(opps_html, st["table_cell"]),
        ],
    ]
    h_table = Table(highlights_data, colWidths=[260, 260])
    h_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f0fdf4")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fffbeb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(h_table)
    story.append(Spacer(1, 16))

    # Competency Scores by Relationship
    story.append(Paragraph("Evaluación por Competencias y Relaciones", st["h2"]))
    comp_headers = [
        Paragraph("Competencia", st["table_header"]),
        Paragraph("Auto", st["table_header"]),
        Paragraph("Evaluadores", st["table_header"]),
        Paragraph("Brecha", st["table_header"]),
        Paragraph("Desglose por Relación", st["table_header"]),
    ]
    comp_rows = [comp_headers]

    for c in p_results.competencies:
        auto_val = f"{c.self_score:.2f}" if c.self_score is not None else "-"
        eval_val = f"{c.evaluators_score:.2f}" if c.evaluators_score is not None else "-"
        gap_val = f"{c.gap:+.2f}" if c.gap is not None else "-"
        
        rel_items = []
        if c.by_relationship:
            for r_name, r_score in c.by_relationship.items():
                rel_items.append(f"<b>{r_name}:</b> {r_score:.2f}")
        rel_str = " | ".join(rel_items) if rel_items else "-"

        comp_rows.append(
            [
                Paragraph(c.competency_name, st["table_cell_bold"]),
                Paragraph(auto_val, st["table_cell_right"]),
                Paragraph(eval_val, st["table_cell_right"]),
                Paragraph(gap_val, st["table_cell_right"]),
                Paragraph(rel_str, st["table_cell"]),
            ]
        )

    comp_table = Table(comp_rows, colWidths=[140, 50, 65, 55, 210])
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r_idx in range(1, len(comp_rows)):
        if r_idx % 2 == 0:
            t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f8fafc")))
    comp_table.setStyle(TableStyle(t_style))
    story.append(comp_table)
    story.append(Spacer(1, 16))

    # Detailed Questions & Qualitative Comments
    story.append(Paragraph("Detalle de Preguntas y Comentarios Cualitativos", st["h2"]))

    questions_with_comments = [q for q in p_results.questions if q.comments]
    
    q_rows = [
        [
            Paragraph("Pregunta", st["table_header"]),
            Paragraph("Competencia", st["table_header"]),
            Paragraph("Auto", st["table_header"]),
            Paragraph("Eval.", st["table_header"]),
        ]
    ]

    for q in p_results.questions:
        q_self = f"{q.self_score:.2f}" if q.self_score is not None else "-"
        q_eval = f"{q.evaluators_score:.2f}" if q.evaluators_score is not None else "-"
        q_rows.append(
            [
                Paragraph(q.question_text, st["table_cell"]),
                Paragraph(q.competency_name, st["table_cell_bold"]),
                Paragraph(q_self, st["table_cell_right"]),
                Paragraph(q_eval, st["table_cell_right"]),
            ]
        )

    q_table = Table(q_rows, colWidths=[270, 130, 60, 60])
    qt_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r_idx in range(1, len(q_rows)):
        if r_idx % 2 == 0:
            qt_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f8fafc")))
    q_table.setStyle(TableStyle(qt_style))
    story.append(q_table)

    if questions_with_comments:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Comentarios Cualitativos Recibidos", st["h2"]))

        for q in questions_with_comments:
            story.append(Paragraph(f"<b>Pregunta:</b> {q.question_text}", st["body_bold"]))
            story.append(Spacer(1, 4))
            
            comm_rows = []
            for c in q.comments:
                rel_badge = f"<font color='#0176d3'><b>[{c.get('relationship', 'Evaluador')}]</b></font>"
                comm_text = c.get("comment", "")
                comm_rows.append([Paragraph(f"{rel_badge} {comm_text}", st["table_cell"])])

            comm_table = Table(comm_rows, colWidths=[520])
            comm_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(comm_table)
            story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_all_participants_zip(db: Session, company_id: UUID, evaluation_id: UUID) -> bytes:
    participants = db.scalars(
        select(Participant).where(
            Participant.company_id == company_id,
            Participant.evaluation_id == evaluation_id,
        )
    ).all()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for p in participants:
            pdf_bytes = generate_participant_results_pdf(db, company_id, evaluation_id, p.id)
            # Sanitize filename
            clean_name = "".join(c for c in p.full_name if c.isalnum() or c in (" ", "_", "-")).rstrip()
            filename = f"Informe_360_{clean_name.replace(' ', '_')}.pdf"
            zip_file.writestr(filename, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# ==============================================================================
# MOTOR DE GENERACIÓN DEL REPORTE EJECUTIVO (29 PÁGINAS EXACTAS)
# ==============================================================================

def _parse_logo_image(logo_str: str | None):
    if not logo_str or not isinstance(logo_str, str):
        return None
    try:
        logo_str = logo_str.strip()
        if logo_str.startswith("data:image"):
            if "," in logo_str:
                _, encoded = logo_str.split(",", 1)
            else:
                encoded = logo_str
            raw = base64.b64decode(encoded)
            return ImageReader(io.BytesIO(raw))
        elif logo_str.startswith("http://") or logo_str.startswith("https://"):
            import urllib.request
            req = urllib.request.Request(logo_str, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return ImageReader(io.BytesIO(resp.read()))
        else:
            raw = base64.b64decode(logo_str)
            return ImageReader(io.BytesIO(raw))
    except Exception as e:
        print(f"Warning: could not parse logo image: {e}")
        return None


class MSDExecutiveCanvas(canvas.Canvas):
    client_logo_reader = None
    consultant_logo_reader = None
    cfg_company_name = "MSD"
    cfg_consultant_name = "abc&co"
    cfg_header_title = "Reporte Grupal - Evaluación 360°"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_cover_client_logo(self, height):
        if getattr(self, "client_logo_reader", None):
            try:
                self.drawImage(
                    self.client_logo_reader,
                    46,
                    height - 95,
                    width=135,
                    height=50,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                return
            except Exception:
                pass
        self.setFillColor(colors.HexColor("#00857c"))
        self.circle(46, height - 70, 10, fill=1, stroke=0)
        self.circle(66, height - 70, 10, fill=1, stroke=0)
        self.circle(56, height - 58, 10, fill=1, stroke=0)
        self.circle(56, height - 82, 10, fill=1, stroke=0)
        self.setFont("Helvetica-Bold", 24)
        cname = getattr(self, "cfg_company_name", "MSD") or "MSD"
        self.drawString(85, height - 78, cname)

    def _draw_header_client_logo(self, height):
        if getattr(self, "client_logo_reader", None):
            try:
                self.drawImage(
                    self.client_logo_reader,
                    42,
                    height - 42,
                    width=65,
                    height=24,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                return
            except Exception:
                pass
        self.setFillColor(colors.HexColor("#00857c"))
        self.circle(42, height - 32, 5, fill=1, stroke=0)
        self.circle(52, height - 32, 5, fill=1, stroke=0)
        self.circle(47, height - 25, 5, fill=1, stroke=0)
        self.circle(47, height - 39, 5, fill=1, stroke=0)
        self.setFont("Helvetica-Bold", 12)
        cname = getattr(self, "cfg_company_name", "MSD") or "MSD"
        self.drawString(62, height - 36, cname)

    def _draw_footer_consultant_logo(self, width):
        if getattr(self, "consultant_logo_reader", None):
            try:
                self.drawImage(
                    self.consultant_logo_reader,
                    width - 110,
                    22,
                    width=74,
                    height=26,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                return
            except Exception:
                pass
        cons_name = getattr(self, "cfg_consultant_name", "abc&co") or "abc&co"
        self.setFont("Helvetica-Bold", 12)
        self.setFillColor(colors.HexColor("#65a30d"))
        self.drawRightString(width - 36, 40, cons_name)
        self.setFont("Helvetica", 5.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(width - 36, 30, "COACHING / CONSULTING")

    def draw_decorations(self, num_pages):
        width, height = letter
        p_num = self._pageNumber
        header_title = getattr(self, "cfg_header_title", "Reporte Grupal - Evaluación 360°") or "Reporte Grupal - Evaluación 360°"

        # Pág 1: Portada
        if p_num == 1:
            self.saveState()
            self._draw_cover_client_logo(height)

            # Ondas vectoriales inferiores de portada
            self.setStrokeColor(colors.HexColor("#94a3b8"))
            self.setLineWidth(0.7)
            for i in range(14):
                p = self.beginPath()
                p.moveTo(width * 0.15 + i * 14, 0)
                p.curveTo(width * 0.35, height * 0.28 + i * 7, width * 0.8, height * 0.42 - i * 6, width, height * 0.22 + i * 11)
                self.drawPath(p, stroke=1, fill=0)

            self.restoreState()
            return

        # Separadores de sección: Páginas 6, 9, 18, 25
        is_separator = p_num in (6, 9, 18, 25)
        if is_separator:
            self.saveState()
            self._draw_header_client_logo(height)

            # Encabezado derecha
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor("#1e293b"))
            self.drawRightString(width - 36, height - 34, header_title)

            # Pie de página: curva decorativa abajo a la izquierda
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            for i in range(5):
                p = self.beginPath()
                p.moveTo(0, 30 + i * 4)
                p.curveTo(40, 10 + i * 5, 80, 60 + i * 3, 140, 20 + i * 4)
                self.drawPath(p, stroke=1, fill=0)

            self._draw_footer_consultant_logo(width)

            # Número de página sutil al centro
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#94a3b8"))
            self.drawCentredString(width / 2.0, 18, f"{p_num}")
            self.restoreState()
            return

        # Páginas normales de contenido (2..5, 7, 8, 10..17, 19..24, 26..29)
        self.saveState()
        self._draw_header_client_logo(height)

        # Top-right title
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#1e293b"))
        self.drawRightString(width - 36, height - 34, header_title)

        # Bottom-left curva decorativa
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        for i in range(5):
            p = self.beginPath()
            p.moveTo(0, 30 + i * 4)
            p.curveTo(40, 10 + i * 5, 80, 60 + i * 3, 140, 20 + i * 4)
            self.drawPath(p, stroke=1, fill=0)

        self._draw_footer_consultant_logo(width)

        # Número de página sutil al centro
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.drawCentredString(width / 2.0, 18, f"{p_num}")
        self.restoreState()


def make_executive_canvas(client_logo=None, consultant_logo=None, company_name="MSD", consultant_name="abc&co", header_title="Reporte Grupal - Evaluación 360°"):
    c_reader = _parse_logo_image(client_logo)
    cons_reader = _parse_logo_image(consultant_logo)

    class DynamicExecutiveCanvas(MSDExecutiveCanvas):
        client_logo_reader = c_reader
        consultant_logo_reader = cons_reader
        cfg_company_name = company_name
        cfg_consultant_name = consultant_name
        cfg_header_title = header_title

    return DynamicExecutiveCanvas


def _get_executive_report_styles():
    base = getSampleStyleSheet()

    c_teal = colors.HexColor("#00857c")
    c_dark = colors.HexColor("#0f172a")
    c_gray = colors.HexColor("#475569")

    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=c_dark,
            spaceAfter=6,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSub",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=c_teal,
            spaceAfter=14,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=c_teal,
            spaceBefore=8,
            spaceAfter=10,
        ),
        "subsection_title": ParagraphStyle(
            "SubSectionTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=c_teal,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "ExecBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "ExecBullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor("#334155"),
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=5,
        ),
        "divider_title_1": ParagraphStyle(
            "DivTitle1",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=c_teal,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "divider_title_2": ParagraphStyle(
            "DivTitle2",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=c_teal,
            alignment=TA_CENTER,
        ),
        "table_head_mini": ParagraphStyle(
            "THMini",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.8,
            leading=7.2,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_CENTER,
        ),
        "table_cell_mini": ParagraphStyle(
            "TCMini",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=5.8,
            leading=7.2,
            textColor=colors.HexColor("#1e293b"),
            alignment=TA_CENTER,
        ),
        "table_cell_mini_left": ParagraphStyle(
            "TCMiniLeft",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=5.8,
            leading=7.2,
            textColor=colors.HexColor("#1e293b"),
            alignment=TA_LEFT,
        ),
    }


def build_executive_29p_report_from_results(results: ExecutiveReportResults) -> bytes:
    sty = _get_executive_report_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25,
    )

    story = []

    cfg = results.report_config or {}
    company_name = cfg.get("company_name") or results.company_name or "MSD"
    consultant_name = cfg.get("consultant_name") or "abc&co"
    header_title = cfg.get("header_title") or "Reporte Grupal - Evaluación 360°"

    th_high = float(results.thresholds.get("high", 8.5)) if results.thresholds else 8.5
    th_med = float(results.thresholds.get("medium", 7.0)) if results.thresholds else 7.0
    label_high = cfg.get("label_high", "excede expectativas")
    label_med = cfg.get("label_med", "cumple expectativas")
    label_low = cfg.get("label_low", "necesita mejora")

    # =========================================================================
    # PÁGINA 1: PORTADA
    # =========================================================================
    cov_t1 = cfg.get("cover_title_1") or "REPORTE DE"
    cov_t2 = cfg.get("cover_title_2") or "EVALUACIÓN"
    cov_t3 = cfg.get("cover_title_3") or "360°"
    cov_s1 = cfg.get("cover_subtitle_1") or "REPORTE GRUPAL"
    cov_s2 = cfg.get("cover_subtitle_2") or f"Fuerza de ventas {company_name}"

    story.append(Spacer(1, 140))
    story.append(Paragraph(cov_t1, sty["cover_title"]))
    story.append(Paragraph(cov_t2, sty["cover_title"]))
    story.append(Paragraph(cov_t3, ParagraphStyle("CoverBig360", parent=sty["cover_title"], fontSize=34, leading=38, textColor=colors.HexColor("#0f172a"))))
    story.append(Spacer(1, 180))
    story.append(Paragraph(cov_s1, ParagraphStyle("CoverRepGrup", parent=sty["cover_subtitle"], fontSize=13, leading=16, alignment=TA_RIGHT)))
    story.append(Paragraph(cov_s2, ParagraphStyle("CoverSubR", parent=sty["cover_subtitle"], fontSize=13, leading=16, alignment=TA_RIGHT)))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: INTRODUCCIÓN Y COMPETENCIAS (PARTE 1)
    # =========================================================================
    intro_1 = cfg.get("intro_p1") or f"En el contexto del proceso de transformación que actualmente atraviesa {company_name}, se llevó a cabo una evaluación estructurada de las competencias clave de la fuerza de ventas, con el propósito de identificar el nivel de madurez individual y grupal, así como detectar oportunidades estratégicas de fortalecimiento."
    intro_2 = cfg.get("intro_p2") or f"El entorno competitivo y la evolución del modelo comercial exigen no solo excelencia operativa, sino también sofisticación analítica, adaptabilidad y capacidad de influencia en entornos cada vez más complejos. Bajo esta premisa, {company_name} definió cuatro competencias críticas alineadas con el modelo de desempeño esperado."
    intro_3 = cfg.get("intro_p3") or "La evaluación fue diseñada bajo un enfoque 360°, incorporando la autoevaluación del representante, la evaluación de su líder directo y la evaluación de dos pares, con el fin de obtener una visión integral y balanceada del desempeño."

    story.append(Paragraph("Introducción", sty["section_title"]))
    story.append(Paragraph(f"• {intro_1}", sty["bullet"]))
    story.append(Paragraph(f"• {intro_2}", sty["bullet"]))
    story.append(Paragraph(f"• {intro_3}", sty["bullet"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph(f"Competencias {company_name}", sty["section_title"]))
    c_names = [c.competency_name for c in results.competencies]
    c1_name = c_names[0] if len(c_names) > 0 else "Excelencia en la ejecución"
    c2_name = c_names[1] if len(c_names) > 1 else "Flexibilidad y capacidad de adaptación"

    story.append(Paragraph(f"<b>1. {c1_name}:</b> Capacidad de ejecutar con consistencia, calidad y precisión para cumplir objetivos de negocio, mantener altos estándares del cumplimiento de nuestras políticas y foco en resultados.", sty["bullet"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>2. {c2_name}:</b> Ajustarse a nuevos entornos, terapias, perfiles médicos y modelos comerciales manteniendo un alto desempeño y la continuidad del negocio.", sty["bullet"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: COMPETENCIAS (PARTE 2), OBJETIVO Y METODOLOGÍA
    # =========================================================================
    c3_name = c_names[2] if len(c_names) > 2 else "Análisis digital y de datos"
    c4_name = c_names[3] if len(c_names) > 3 else "Influencia y gestión de clientes externos"

    story.append(Paragraph(f"<b>3. {c3_name}:</b> Capacidad de interpretar y tomar decisiones estratégicas basadas en datos, contexto y oportunidad, priorizando acciones que maximicen el impacto del negocio.", sty["bullet"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>4. {c4_name}:</b> Habilidad para generar impacto positivo, credibilidad y confianza con médicos, líderes hospitalarios, compras, líderes de opinión \"KOLs\" y decisores.", sty["bullet"]))
    story.append(Spacer(1, 14))

    obj_main = cfg.get("objectives_main") or "Evaluar el nivel de desarrollo y homogeneidad de las competencias clave de la fuerza de ventas, identificando fortalezas consolidadas y brechas estratégicas en el contexto del proceso de transformación organizacional."

    story.append(Paragraph("Objetivo del Reporte Grupal", sty["section_title"]))
    story.append(Paragraph(obj_main, sty["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("De manera más específica, este reporte busca:", sty["body"]))
    story.append(Paragraph("1. Determinar el nivel promedio de desarrollo de cada competencia evaluada.", sty["bullet"]))
    story.append(Paragraph("2. Analizar la consistencia interna del desempeño (mediana y dispersión).", sty["bullet"]))
    story.append(Paragraph("3. Identificar comportamientos específicos con mayor oportunidad de mejora.", sty["bullet"]))
    story.append(Paragraph("4. Generar insumos para la priorización de intervenciones de desarrollo.", sty["bullet"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Metodología", sty["section_title"]))
    tot_eval = results.total_evaluados
    lines_str = ", ".join([b.line_name for b in results.business_lines]) or "Diabetes, Especialidades y Sotatercep"
    story.append(Paragraph(f"La evaluación de competencias 360° fue aplicada a la totalidad de los representantes médicos de {company_name} ({tot_eval} personas, distribuidas en las líneas: {lines_str}) a través de una encuesta estructurada basada en comportamientos observables.", sty["body"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: METODOLOGÍA (CONT.) Y LINEAMIENTOS PARA LA LECTURA
    # =========================================================================
    story.append(Paragraph("estructurada basada en comportamientos observables asociados a cada competencia. Así mismo, está integrada por tres perspectivas complementarias:", sty["body"]))
    story.append(Paragraph("• <b>Autoevaluación del representante:</b> cómo se percibe la persona en su rol.", sty["bullet"]))
    story.append(Paragraph("• <b>Evaluación del líder directo:</b> cómo es observado por quien lo lidera y orienta su desempeño.", sty["bullet"]))
    story.append(Paragraph("• <b>Evaluación de pares (2):</b> cómo es observado por colegas en la operación diaria.", sty["bullet"]))
    story.append(Spacer(1, 8))
    q_count = len(results.questions) or 33
    story.append(Paragraph(f"Esta evaluación está compuesta por {q_count} reactivos con una escala cuantitativa de desempeño en un rango de 1 a 10 para su valoración.", sty["body"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Lineamientos para la lectura del reporte", sty["section_title"]))
    story.append(Paragraph("Puntaje neto", sty["subsection_title"]))
    story.append(Paragraph("Representa el promedio integrado de todas las fuentes (autoevaluación, líder y pares). Refleja qué tan sólida y consistente es una competencia en la práctica cotidiana, se utilizó la siguiente escala:", sty["body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"• <b>Mayor o igual a {th_high:.1f}:</b> se debe interpretar como una competencia consolidada y diferenciada, es decir, <b>{label_high}</b>.", sty["bullet"]))
    story.append(Paragraph(f"• <b>Entre {th_med:.1f} y {th_high - 0.1:.1f}:</b> indica un desempeño funcional adecuado, con oportunidades de consistencia, es decir, <b>{label_med}</b>.", sty["bullet"]))
    story.append(Paragraph(f"• <b>Menor o igual a {th_med - 0.1:.1f}:</b> indica la existencia de una brecha relevante que requiere intervención, es decir, <b>{label_low}</b>.", sty["bullet"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 5: PUNTAJE PONDERADO
    # =========================================================================
    story.append(Paragraph("Puntaje ponderado", sty["section_title"]))
    story.append(Paragraph(f"{company_name} estableció la siguiente ponderación para cada una de las cuatro competencias evaluadas:", sty["body"]))
    story.append(Spacer(1, 8))

    for c in results.competencies:
        story.append(Paragraph(f"• <b>{c.competency_name}:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>{c.weight_pct:.0f}%</b>", sty["bullet"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph("Estos pesos reflejan la relevancia estratégica de cada competencia dentro del rol y conforman, en conjunto, una valoración total ponderada del 100%. El puntaje ponderado integra el nivel de la competencia y la relevancia estratégica, permitiendo priorizar acciones de desarrollo con impacto en el negocio.", sty["body"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 6: SEPARADOR - REPORTE EJECUTIVO / PRINCIPALES HALLAZGOS
    # =========================================================================
    story.append(Spacer(1, 240))
    story.append(Paragraph("REPORTE EJECUTIVO", sty["divider_title_1"]))
    story.append(Paragraph("PRINCIPALES HALLAZGOS", sty["divider_title_2"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 7: PRINCIPALES HALLAZGOS & TABLA RESUMEN ESTADÍSTICO
    # =========================================================================
    story.append(Paragraph("Principales hallazgos", sty["section_title"]))
    for b in results.insights.summary_bullets:
        story.append(Paragraph(f"• {b}", sty["bullet"]))
    story.append(Spacer(1, 24))

    h_row = [Paragraph("<b>Métrica</b>", sty["table_head_mini"])]
    for c in results.competencies:
        h_row.append(Paragraph(f"<b>{c.competency_name}</b>", sty["table_head_mini"]))
    h_row.append(Paragraph("<b>Total</b>", sty["table_head_mini"]))

    r_prom = [Paragraph("<b>Promedio</b>", sty["table_cell_mini_left"])]
    for c in results.competencies:
        r_prom.append(Paragraph(f"{c.net_average:.2f}", sty["table_cell_mini"]))
    r_prom.append(Paragraph(f"{results.net_overall.get('average', 0.0):.2f}", sty["table_cell_mini"]))

    r_med = [Paragraph("<b>Mediana</b>", sty["table_cell_mini_left"])]
    for c in results.competencies:
        r_med.append(Paragraph(f"{c.net_median:.2f}", sty["table_cell_mini"]))
    r_med.append(Paragraph(f"{results.net_overall.get('median', 0.0):.2f}", sty["table_cell_mini"]))

    r_std = [Paragraph("<b>Desviación Estándar</b>", sty["table_cell_mini_left"])]
    for c in results.competencies:
        r_std.append(Paragraph(f"{c.net_stddev:.2f}", sty["table_cell_mini"]))
    r_std.append(Paragraph(f"{results.net_overall.get('stddev', 0.0):.2f}", sty["table_cell_mini"]))

    stat_table = Table([h_row, r_prom, r_med, r_std], colWidths=[90, 85, 85, 85, 85, 70])
    stat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#00857c")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(stat_table)
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 8: DESARROLLO DE LAS COMPETENCIAS (REACTIVOS)
    # =========================================================================
    c_items_data = []
    for c in results.competencies:
        c_items_data.append({
            "name": c.competency_name,
            "items": [{"text": it.question_text, "average": it.average} for it in c.items]
        })
    img_items = generate_competency_items_chart(c_items_data, width_inches=8.0, height_inches=5.0)
    story.append(Image(io.BytesIO(img_items), width=510, height=340))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Considerando la gráfica de \"Desarrollo de competencias\":", sty["body"]))
    for b in results.insights.reactivos_bullets:
        story.append(Paragraph(f"• {b}", sty["bullet"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 9: SEPARADOR - RESULTADOS / PUNTAJE NETO
    # =========================================================================
    story.append(Spacer(1, 240))
    story.append(Paragraph("Resultados", sty["divider_title_1"]))
    story.append(Paragraph("Puntaje neto", sty["divider_title_2"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 10: RANKING INDIVIDUAL Y DESEMPEÑO (2023-2025) - PUNTAJE NETO
    # =========================================================================
    story.append(Paragraph("<b>Ranking individual y Evaluación de Desempeño (2023-2025)</b>", ParagraphStyle("TblTitle", parent=sty["section_title"], fontSize=10, leading=12, spaceAfter=3, spaceBefore=0)))

    t10_headers = ["Rol", "Línea", "Nombre"]
    for c in results.competencies:
        t10_headers.append(c.competency_name[:12])
    t10_headers.append("Prom.")
    t10_headers.extend(["2023", "2024", "2025"])

    t10_rows = [t10_headers]
    t10_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 0), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ]

    for r_idx, p in enumerate(results.participants_matrix, start=1):
        row = [
            p.role or "SR",
            (p.business_line or "General")[:14],
            p.participant_name[:24],
        ]
        for c_idx, c in enumerate(results.competencies, start=3):
            val = p.net_scores.get(c.competency_name, 0.0)
            row.append(f"{val:.2f}")
            if val >= th_high:
                t10_styles.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#dcfce7")))
                t10_styles.append(("TEXTCOLOR", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#15803d")))
            elif val >= th_med:
                t10_styles.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#fef9c3")))
                t10_styles.append(("TEXTCOLOR", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#854d0e")))
            else:
                t10_styles.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#fee2e2")))
                t10_styles.append(("TEXTCOLOR", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#b91c1c")))

        avg_idx = 3 + len(results.competencies)
        row.append(f"{p.net_average:.2f}")
        t10_styles.append(("FONTNAME", (avg_idx, r_idx), (avg_idx, r_idx), "Helvetica-Bold"))
        t10_styles.append(("BACKGROUND", (avg_idx, r_idx), (avg_idx, r_idx), colors.HexColor("#e0f2fe")))

        row.append(p.performance_history.get("2023", "#N/D"))
        row.append(p.performance_history.get("2024", "#N/D"))
        row.append(p.performance_history.get("2025", "#N/D"))
        t10_rows.append(row)

    col_w = [22, 60, 115] + [42] * len(results.competencies) + [38, 49, 49, 49]
    t10 = Table(t10_rows, colWidths=col_w, rowHeights=[11.5] * len(t10_rows))
    t10.setStyle(TableStyle(t10_styles))
    story.append(t10)
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 11: RANKING GENERAL CONTRA MEDIANA (NETO)
    # =========================================================================
    p_pairs_net = [(p.participant_name, p.net_average) for p in results.participants_matrix]
    net_med = results.net_overall.get("median", 8.90)
    net_std = results.net_overall.get("stddev", 0.35)
    img_rank_net = generate_ranking_bars_chart(
        title="Ranking Individual de Evaluación – Comparativo contra Mediana",
        participants=p_pairs_net,
        median_val=net_med,
        stddev_val=net_std,
        is_weighted=False,
        width_inches=7.2,
        height_inches=7.8,
    )
    story.append(Image(io.BytesIO(img_rank_net), width=510, height=540))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Mediana:</b> {net_med:.2f} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Desviación estándar:</b> {net_std:.2f}", sty["body"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINAS 12 A 15: RANKINGS POR COMPETENCIA CONTRA MEDIANA (NETO)
    # =========================================================================
    for c in results.competencies:
        p_pairs_c = [(p.participant_name, p.net_scores.get(c.competency_name, 0.0)) for p in results.participants_matrix]
        img_c = generate_ranking_bars_chart(
            title=f"{c.competency_name}",
            participants=p_pairs_c,
            median_val=c.net_median,
            stddev_val=c.net_stddev,
            is_weighted=False,
            width_inches=7.2,
            height_inches=7.8,
        )
        story.append(Paragraph(f"<b>Ranking Individual de Evaluación por competencia – Comparativo contra Mediana</b>", ParagraphStyle("RSub", parent=sty["section_title"], fontSize=9.5, leading=11, spaceAfter=2)))
        story.append(Image(io.BytesIO(img_c), width=510, height=530))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Mediana:</b> {c.net_median:.2f} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Desviación estándar:</b> {c.net_stddev:.2f}", sty["body"]))
        story.append(PageBreak())

    # =========================================================================
    # PÁGINA 16: GRÁFICAS DE DISPERSIÓN POR COMPETENCIA (NETO) - C1 Y C2
    # =========================================================================
    story.append(Paragraph("Gráficas de dispersión por Competencia", ParagraphStyle("GTit", parent=sty["section_title"], spaceAfter=4)))
    story.append(Paragraph("La fuerza de ventas de MSD muestra un perfil de alto desempeño y estabilidad, con una fortaleza clara en adaptabilidad y ejecución. La principal oportunidad de desarrollo está en Análisis digital y de datos, no por bajo desempeño crítico, sino por mayor dispersión y menor promedio relativo frente a las demás competencias.", ParagraphStyle("GBod", parent=sty["body"], spaceAfter=4)))

    pts_c1 = [(pt.index, pt.net_score) for pt in results.scatter_data.get(c1_name, [])]
    img_sc1 = generate_scatter_plot(c1_name, pts_c1, results.competencies[0].net_median if len(results.competencies) > 0 else 8.91, width_inches=6.8, height_inches=3.0)
    story.append(Image(io.BytesIO(img_sc1), width=490, height=225))
    story.append(Spacer(1, 4))

    pts_c2 = [(pt.index, pt.net_score) for pt in results.scatter_data.get(c2_name, [])]
    img_sc2 = generate_scatter_plot(c2_name, pts_c2, results.competencies[1].net_median if len(results.competencies) > 1 else 9.15, width_inches=6.8, height_inches=3.0)
    story.append(Image(io.BytesIO(img_sc2), width=490, height=225))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 17: GRÁFICAS DE DISPERSIÓN POR COMPETENCIA (NETO) - C3 Y C4
    # =========================================================================
    pts_c3 = [(pt.index, pt.net_score) for pt in results.scatter_data.get(c3_name, [])]
    img_sc3 = generate_scatter_plot(c3_name, pts_c3, results.competencies[2].net_median if len(results.competencies) > 2 else 8.71, width_inches=6.8, height_inches=3.3)
    story.append(Image(io.BytesIO(img_sc3), width=490, height=245))
    story.append(Spacer(1, 8))

    pts_c4 = [(pt.index, pt.net_score) for pt in results.scatter_data.get(c4_name, [])]
    img_sc4 = generate_scatter_plot(c4_name, pts_c4, results.competencies[3].net_median if len(results.competencies) > 3 else 8.98, width_inches=6.8, height_inches=3.3)
    story.append(Image(io.BytesIO(img_sc4), width=490, height=245))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 18: SEPARADOR - RESULTADOS / PUNTAJE PONDERADO
    # =========================================================================
    story.append(Spacer(1, 240))
    story.append(Paragraph("Resultados", sty["divider_title_1"]))
    story.append(Paragraph("Puntaje ponderado", sty["divider_title_2"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 19: RANKING INDIVIDUAL PONDERADO Y DESEMPEÑO (2023-2025)
    # =========================================================================
    story.append(Paragraph("<b>Ranking individual Ponderado y Evaluación de Desempeño (2023-2025)</b>", ParagraphStyle("TblTitleP", parent=sty["section_title"], fontSize=10, leading=12, spaceAfter=3, spaceBefore=0)))

    t19_rows = [t10_headers]
    t19_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 0), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ]

    for r_idx, p in enumerate(results.participants_matrix, start=1):
        row = [
            p.role or "SR",
            (p.business_line or "General")[:14],
            p.participant_name[:24],
        ]
        for c_idx, c in enumerate(results.competencies, start=3):
            val = p.weighted_scores.get(c.competency_name, 0.0)
            row.append(f"{val:.2f}")

        tot_idx = 3 + len(results.competencies)
        row.append(f"{p.weighted_total:.2f}")
        t19_styles.append(("FONTNAME", (tot_idx, r_idx), (tot_idx, r_idx), "Helvetica-Bold"))
        t19_styles.append(("BACKGROUND", (tot_idx, r_idx), (tot_idx, r_idx), colors.HexColor("#e0f2fe")))

        row.append(p.performance_history.get("2023", "#N/D"))
        row.append(p.performance_history.get("2024", "#N/D"))
        row.append(p.performance_history.get("2025", "#N/D"))
        t19_rows.append(row)

    t19 = Table(t19_rows, colWidths=col_w, rowHeights=[11.5] * len(t19_rows))
    t19.setStyle(TableStyle(t19_styles))
    story.append(t19)
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 20: RANKING INDIVIDUAL PONDERADO GENERAL CONTRA MEDIANA
    # =========================================================================
    p_pairs_w = [(p.participant_name, p.weighted_total) for p in results.participants_matrix]
    w_med = results.weighted_overall.get("median", 8.93)
    w_std = results.weighted_overall.get("stddev", 0.35)
    img_rank_w = generate_ranking_bars_chart(
        title="Ranking Individual de Evaluación – Comparativo contra Mediana",
        participants=p_pairs_w,
        median_val=w_med,
        stddev_val=w_std,
        is_weighted=True,
        width_inches=7.2,
        height_inches=7.8,
    )
    story.append(Image(io.BytesIO(img_rank_w), width=510, height=540))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Mediana:</b> {w_med:.2f} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Desviación estándar:</b> {w_std:.2f}", sty["body"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINAS 21 A 24: RANKINGS PONDERADOS POR COMPETENCIA CONTRA MEDIANA
    # =========================================================================
    for c in results.competencies:
        p_pairs_cw = [(p.participant_name, p.weighted_scores.get(c.competency_name, 0.0)) for p in results.participants_matrix]
        img_cw = generate_ranking_bars_chart(
            title=f"{c.competency_name}",
            participants=p_pairs_cw,
            median_val=c.weighted_median,
            stddev_val=c.weighted_stddev,
            is_weighted=True,
            width_inches=7.2,
            height_inches=7.8,
        )
        story.append(Paragraph(f"<b>Ranking Individual de Evaluación por competencia – Comparativo contra Mediana</b>", ParagraphStyle("RSubP", parent=sty["section_title"], fontSize=9.5, leading=11, spaceAfter=2)))
        story.append(Image(io.BytesIO(img_cw), width=510, height=530))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Mediana:</b> {c.weighted_median:.2f} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Desviación estándar:</b> {c.weighted_stddev:.2f}", sty["body"]))
        story.append(PageBreak())

    # =========================================================================
    # PÁGINA 25: SEPARADOR - RESULTADOS POR LÍNEA
    # =========================================================================
    story.append(Spacer(1, 250))
    story.append(Paragraph("Resultados por línea", sty["divider_title_2"]))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 26: RANKING INDIVIDUAL POR LÍNEA - PUNTAJE NETO
    # =========================================================================
    story.append(Paragraph("<b>Ranking individual por Línea- Puntaje Neto</b>", ParagraphStyle("LTitle", parent=sty["section_title"], fontSize=10, leading=12, spaceAfter=2, spaceBefore=0)))
    story.append(Paragraph("Los representantes con mayor puntaje neto forman parte de la línea de Diabetes y Especialidades.", ParagraphStyle("LSub", parent=sty["body"], spaceAfter=3)))

    t26_rows = [t10_headers]
    t26_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 0), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ]

    sorted_by_line = sorted(results.participants_matrix, key=lambda p: (p.business_line or "General", -p.net_average))

    for r_idx, p in enumerate(sorted_by_line, start=1):
        row = [
            p.role or "SR",
            (p.business_line or "General")[:14],
            p.participant_name[:24],
        ]
        for c_idx, c in enumerate(results.competencies, start=3):
            val = p.weighted_scores.get(c.competency_name, 0.0)
            row.append(f"{val:.2f}")

        tot_idx = 3 + len(results.competencies)
        row.append(f"{p.weighted_total:.2f}")
        t26_styles.append(("FONTNAME", (tot_idx, r_idx), (tot_idx, r_idx), "Helvetica-Bold"))
        t26_styles.append(("BACKGROUND", (tot_idx, r_idx), (tot_idx, r_idx), colors.HexColor("#e0f2fe")))

        row.append(p.performance_history.get("2023", "#N/D"))
        row.append(p.performance_history.get("2024", "#N/D"))
        row.append(p.performance_history.get("2025", "#N/D"))
        t26_rows.append(row)

    t26 = Table(t26_rows, colWidths=col_w, rowHeights=[11.5] * len(t26_rows))
    t26.setStyle(TableStyle(t26_styles))
    story.append(t26)
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 27: GRÁFICAS DE DISPERSIÓN POR LÍNEA - COMPETENCIA 1
    # =========================================================================
    story.append(Paragraph("Gráficas de dispersión por Competencia", ParagraphStyle("GT2", parent=sty["section_title"], spaceAfter=4)))
    story.append(Paragraph("El análisis de dispersión por competencia evidencia un desempeño sólido y consistente a nivel general; no obstante, se identifican diferencias de tendencia entre las unidades de negocio. En particular, Excelencia en la ejecución y Análisis digital y de datos muestran variaciones más marcadas entre Diabetes, Especialidades y Sotatercep, lo que sugiere distintos niveles de madurez en estas capacidades. Por el contrario, Flexibilidad y capacidad de adaptación e Influencia y gestión de clientes externos presentan comportamientos homogéneos y estables, consolidándose como fortalezas transversales del equipo.", ParagraphStyle("GB2", parent=sty["body"], spaceAfter=6)))

    seg_c1 = []
    for b_line in results.business_lines:
        line_pts = [(idx + 1, p.weighted_scores.get(c1_name, 0.0)) for idx, p in enumerate(b_line.participants)]
        seg_c1.append({"name": b_line.line_name, "points": line_pts})
    img_seg1 = generate_segmented_scatter_plot(c1_name, seg_c1, results.competencies[0].weighted_median if len(results.competencies) > 0 else 3.12, y_min=2.5, y_max=3.6, width_inches=6.8, height_inches=3.6)
    story.append(Image(io.BytesIO(img_seg1), width=500, height=310))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 28: GRÁFICAS DE DISPERSIÓN POR LÍNEA - COMPETENCIA 2 Y 3
    # =========================================================================
    seg_c2 = []
    for b_line in results.business_lines:
        line_pts = [(idx + 1, p.weighted_scores.get(c2_name, 0.0)) for idx, p in enumerate(b_line.participants)]
        seg_c2.append({"name": b_line.line_name, "points": line_pts})
    img_seg2 = generate_segmented_scatter_plot(c2_name, seg_c2, results.competencies[1].weighted_median if len(results.competencies) > 1 else 2.75, y_min=2.0, y_max=3.1, width_inches=6.8, height_inches=3.2)
    story.append(Image(io.BytesIO(img_seg2), width=490, height=240))
    story.append(Spacer(1, 6))

    seg_c3 = []
    for b_line in results.business_lines:
        line_pts = [(idx + 1, p.weighted_scores.get(c3_name, 0.0)) for idx, p in enumerate(b_line.participants)]
        seg_c3.append({"name": b_line.line_name, "points": line_pts})
    img_seg3 = generate_segmented_scatter_plot(c3_name, seg_c3, results.competencies[2].weighted_median if len(results.competencies) > 2 else 1.74, y_min=1.0, y_max=2.1, width_inches=6.8, height_inches=3.2)
    story.append(Image(io.BytesIO(img_seg3), width=490, height=240))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 29: GRÁFICA DE DISPERSIÓN POR LÍNEA - COMPETENCIA 4
    # =========================================================================
    seg_c4 = []
    for b_line in results.business_lines:
        line_pts = [(idx + 1, p.weighted_scores.get(c4_name, 0.0)) for idx, p in enumerate(b_line.participants)]
        seg_c4.append({"name": b_line.line_name, "points": line_pts})
    img_seg4 = generate_segmented_scatter_plot(c4_name, seg_c4, results.competencies[3].weighted_median if len(results.competencies) > 3 else 1.35, y_min=1.0, y_max=1.8, width_inches=7.0, height_inches=4.2)
    story.append(Image(io.BytesIO(img_seg4), width=500, height=340))

    # Construir documento final con canvas dinámico configurado
    canvas_cls = make_executive_canvas(
        client_logo=results.client_logo_url,
        consultant_logo=results.consultant_logo_url,
        company_name=company_name,
        consultant_name=consultant_name,
        header_title=header_title,
    )
    doc.build(story, canvasmaker=canvas_cls)
    buffer.seek(0)
    return buffer.getvalue()


def generate_executive_29p_report_pdf(db: Session, company_id: UUID, evaluation_id: UUID) -> bytes:
    results = calculate_executive_report_results(db, company_id, evaluation_id)
    return build_executive_29p_report_from_results(results)

