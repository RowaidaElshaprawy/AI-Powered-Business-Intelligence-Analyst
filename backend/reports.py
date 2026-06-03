"""
PDF report generation using ReportLab (pure Python, no external binary needed).
"""
from __future__ import annotations
import io
from datetime import datetime
import pandas as pd

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles    import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units     import cm
    from reportlab.lib           import colors
    from reportlab.platypus      import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


def generate_pdf_report_bytes(
    df:           pd.DataFrame,
    chat_history: list[dict],
    extra_notes:  str = "",
) -> bytes:
    """Return a PDF as bytes, ready for st.download_button."""

    if not REPORTLAB_OK:
        return _fallback_pdf(df, chat_history, extra_notes)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1a1f36"),
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2d3a8c"),
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body2",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2c2c2c"),
    )
    muted_style = ParagraphStyle(
        "Muted",
        parent=body_style,
        fontSize=9,
        textColor=colors.HexColor("#888888"),
    )

    story = []

    # ── cover ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("Executive Business Intelligence Report", title_style))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        muted_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2d3a8c"), spaceAfter=10))

    # ── KPI summary ────────────────────────────────────────────────────────────
    story.append(Paragraph("Key Performance Indicators", h2_style))
    rev   = df["revenue"].sum()  if "revenue"  in df.columns else 0
    prof  = df["profit"].sum()   if "profit"   in df.columns else 0
    rows  = len(df)
    prods = df["product"].nunique() if "product" in df.columns else "N/A"
    margin = prof / rev * 100 if rev else 0

    kpi_data = [
        ["Metric", "Value"],
        ["Total Revenue",    f"${rev:,.0f}"],
        ["Total Profit",     f"${prof:,.0f}"],
        ["Profit Margin",    f"{margin:.1f}%"],
        ["Total Records",    f"{rows:,}"],
        ["Unique Products",  str(prods)],
    ]
    kpi_table = Table(kpi_data, colWidths=[8*cm, 8*cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2d3a8c")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f3ff"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("ALIGN",       (1, 1), (-1, -1), "RIGHT"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5*cm))

    # ── revenue by product ─────────────────────────────────────────────────────
    if "product" in df.columns and "revenue" in df.columns:
        story.append(Paragraph("Revenue by Product", h2_style))
        grp  = df.groupby("product")["revenue"].sum().sort_values(ascending=False).reset_index()
        pdata = [["Product", "Revenue", "% of Total"]]
        for _, row in grp.iterrows():
            pct = row["revenue"] / rev * 100 if rev else 0
            pdata.append([row["product"], f"${row['revenue']:,.0f}", f"{pct:.1f}%"])
        ptable = Table(pdata, colWidths=[6*cm, 5*cm, 5*cm])
        ptable.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#4f8ef7")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f7f9ff"), colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING",     (0, 0), (-1, -1), 7),
            ("ALIGN",       (1, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(ptable)
        story.append(Spacer(1, 0.4*cm))

    # ── revenue by region ─────────────────────────────────────────────────────
    if "region" in df.columns and "revenue" in df.columns:
        story.append(Paragraph("Revenue by Region", h2_style))
        rgrp = df.groupby("region")["revenue"].sum().sort_values(ascending=False).reset_index()
        rdata = [["Region", "Revenue", "% of Total"]]
        for _, row in rgrp.iterrows():
            pct = row["revenue"] / rev * 100 if rev else 0
            rdata.append([row["region"], f"${row['revenue']:,.0f}", f"{pct:.1f}%"])
        rtable = Table(rdata, colWidths=[6*cm, 5*cm, 5*cm])
        rtable.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#a78bfa")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#faf8ff"), colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING",     (0, 0), (-1, -1), 7),
            ("ALIGN",       (1, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(rtable)
        story.append(Spacer(1, 0.4*cm))

    # ── AI chat insights ──────────────────────────────────────────────────────
    ai_messages = [m for m in chat_history if m["role"] == "assistant"]
    if ai_messages:
        story.append(Paragraph("AI-Generated Insights", h2_style))
        for i, m in enumerate(ai_messages[-3:], 1):  # last 3 AI responses
            story.append(Paragraph(f"Insight {i}:", ParagraphStyle(
                "InsightLabel", parent=body_style, fontName="Helvetica-Bold",
            )))
            # strip markdown-ish characters for PDF
            clean = m["content"].replace("**", "").replace("*", "•").replace("#", "")
            story.append(Paragraph(clean[:1500], body_style))
            story.append(Spacer(1, 0.3*cm))

    # ── extra notes ───────────────────────────────────────────────────────────
    if extra_notes.strip():
        story.append(Paragraph("Additional Notes", h2_style))
        story.append(Paragraph(extra_notes, body_style))
        story.append(Spacer(1, 0.3*cm))

    # ── footer line ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceBefore=10))
    story.append(Paragraph(
        "Confidential — AI-Powered Business Intelligence Analyst",
        muted_style,
    ))

    doc.build(story)
    return buf.getvalue()


def _fallback_pdf(df: pd.DataFrame, chat_history: list[dict], extra_notes: str) -> bytes:
    """Minimal plain-text PDF using fpdf2 when ReportLab is unavailable."""
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Executive BI Report", ln=True, align="C")
        pdf.set_font("Helvetica", size=11)
        rev  = df["revenue"].sum() if "revenue" in df.columns else 0
        prof = df["profit"].sum()  if "profit"  in df.columns else 0
        pdf.ln(5)
        pdf.cell(0, 8, f"Total Revenue: ${rev:,.0f}", ln=True)
        pdf.cell(0, 8, f"Total Profit:  ${prof:,.0f}", ln=True)
        for m in [m for m in chat_history if m["role"] == "assistant"][-2:]:
            pdf.ln(4)
            pdf.multi_cell(0, 7, m["content"][:800])
        if extra_notes:
            pdf.ln(4)
            pdf.multi_cell(0, 7, extra_notes)
        return pdf.output()  # returns bytes in fpdf2
    except Exception as e:
        return f"PDF generation failed: {e}".encode()
