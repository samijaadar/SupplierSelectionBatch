from typing import List
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os


def prepare_table(df, font_size=7):
    """Create a compact, styled data table."""
    data = [df.columns.tolist()] + df.values.tolist()
    col_widths = [4.3 * inch / len(df.columns)] * len(df.columns)

    table = Table(data, colWidths=col_widths, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4053")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F2F3F4")]),
    ]))
    return table


def split_df(df):
    """Split dataframe into smaller metric tables."""
    dfs = {}
    for col in df.columns[1:-1]:
        dfs[col] = df[[df.columns[0], col]]
    return dfs


def create_radar_chart(initial_df, top10_suppliers):
    """Generate a radar chart image for top 10 suppliers using their metrics."""
    # Filter for top suppliers
    radar_data = initial_df[initial_df[initial_df.columns[0]].isin(top10_suppliers)]

    metrics = list(initial_df.columns[1:-1])
    num_vars = len(metrics)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    # Create plot
    plt.figure(figsize=(9, 6))
    ax = plt.subplot(111, polar=True)

    # Draw each supplier’s metrics
    for _, row in radar_data.iterrows():
        values = row[metrics].tolist()
        values += values[:1]  # close loop
        ax.plot(angles, values, label=row[initial_df.columns[0]], linewidth=1)
        ax.fill(angles, values, alpha=0.1)

    # Format
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=8)
    ax.set_rlabel_position(0)
    ax.tick_params(colors="#444444")
    ax.set_title("Top 10 Suppliers Radar Chart (from Initial Dataset)", fontsize=12, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=7)

    # Save temporary image
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.tight_layout()
    plt.savefig(tmp_img.name, dpi=150)
    plt.close()
    return tmp_img.name


def generate_report(initial_df, perturbation, perturbated_df, report_file):
    """Generate a 3-page professional PDF report (with radar chart on 3rd page)."""
    doc = SimpleDocTemplate(
        report_file,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "Heading", parent=styles["Heading3"],
        textColor=colors.HexColor("#1B4F72"), fontSize=9
    )
    normal = ParagraphStyle(
        "NormalSmall", parent=styles["Normal"],
        fontSize=7, leading=8
    )

    # --- PAGE 1 ---
    title = Paragraph("<b>Supplier Selection Analysis Report</b>", styles["Title"])
    intro = Paragraph(
        "This landscape grid report summarizes supplier rankings under normal and perturbed conditions.",
        normal
    )

    # Prepare tables
    initial_ranking = initial_df[[initial_df.columns[0], initial_df.columns[-1]]].head(10)
    initial_ranking.insert(0, "Rank", range(1, len(initial_ranking) + 1))
    tbl_initial = prepare_table(initial_ranking)

    final_ranking = perturbated_df[[perturbated_df.columns[0], perturbated_df.columns[-1]]].head(10)
    final_ranking.insert(0, "Rank", range(1, len(final_ranking) + 1))
    tbl_final = prepare_table(final_ranking)

    dfs = split_df(initial_df)
    metric_tables = []
    for col, sub_df in dfs.items():
        top5 = sub_df.sort_values(by=sub_df.columns[1], ascending=True).head(5)
        top5.insert(0, "Rank", range(1, len(top5) + 1))
        metric_tables.append(Paragraph(f"<b>{col}</b>", heading))
        metric_tables.append(prepare_table(top5))

    # Metric grid layout
    metric_grid_data = []
    chunk_size = 2
    for i in range(0, len(metric_tables), chunk_size * 2):
        row = []
        for j in range(chunk_size):
            idx = i + j * 2
            if idx < len(metric_tables):
                row.append(Table(
                    [[metric_tables[idx]], [metric_tables[idx + 1]]],
                    style=[("ALIGN", (0, 0), (-1, -1), "CENTER")]
                ))
            else:
                row.append("")
        metric_grid_data.append(row)

    metric_grid = Table(metric_grid_data, colWidths=[4.5 * inch, 4.5 * inch])
    metric_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    top_grid = Table([
        [
            Table([[Paragraph("<b>Overall Ranking</b>", heading)], [tbl_initial]]),
            Table([[Paragraph("<b>After Perturbation</b>", heading)], [tbl_final]])
        ]
    ], colWidths=[4.5 * inch, 4.5 * inch])
    top_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))

    elements = [title, intro, Spacer(1, 8), top_grid, Spacer(1, 6),
                Paragraph("<b>Metric-Based Rankings</b>", heading), metric_grid, PageBreak()]

    # --- PAGE 2 ---
    elements.append(Paragraph("<b>Perturbation Scenario</b>", heading))
    elements.append(Paragraph(str(perturbation), normal))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Ranking After Perturbation</b>", heading))
    elements.append(tbl_final)
    elements.append(PageBreak())



    # --- PAGE 3 (Radar Chart) ---
    top10_suppliers = perturbated_df.iloc[:10, 0].tolist()
    radar_path = create_radar_chart(initial_df, top10_suppliers)
    elements.append(Paragraph("<b>Radar Chart of Top 10 Suppliers After Perturbation</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Image(radar_path, width=9 * inch, height=6 * inch))

    # Footer
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        footer_text = f"Generated on {datetime.now():%Y-%m-%d %H:%M} | Page {doc.page}"
        canvas.drawCentredString(landscape(A4)[0] / 2, 0.45 * inch, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)

    # Cleanup temp image
    os.remove(radar_path)
