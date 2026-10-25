"""Render the TP3 classification-question document as a paginated PDF."""
from __future__ import annotations

import argparse
import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def inline_markdown(value: str) -> str:
    text = escape(" ".join(value.split()))
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    return text


def section_body(source: str, heading: str, next_heading: str | None) -> str:
    body = source.split(heading, 1)[1]
    if next_heading:
        body = body.split(next_heading, 1)[0]
    return body.strip()


def paragraphs(value: str) -> list[str]:
    return [piece.strip() for piece in value.split("\n\n") if piece.strip()]


def draw_footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(18 * mm, 16 * mm, width - 18 * mm, 16 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(18 * mm, 11 * mm, "EcomShield | TP3 | Dados")
    canvas.drawRightString(width - 18 * mm, 11 * mm, f"{document.page}")
    canvas.restoreState()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("reports/tp3_data/pergunta_classificacao.md"))
    parser.add_argument("--output", type=Path, default=Path("output/pdf/tp3_pergunta_classificacao.pdf"))
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    table_rows = re.findall(r"`([a-z_]+)` \(([0-9.]+)\)", source)
    if len(table_rows) != 46:
        raise ValueError("A tabela de distribuição precisa listar as 46 intenções.")

    title_style = ParagraphStyle(
        "Title", fontName="Helvetica-Bold", fontSize=15, leading=18,
        textColor=colors.HexColor("#102A43"), spaceAfter=9,
    )
    heading_style = ParagraphStyle(
        "Heading", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
        textColor=colors.HexColor("#174A6E"), spaceBefore=10, spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=8.5, leading=11.7,
        textColor=colors.HexColor("#1E293B"), spaceAfter=6, alignment=TA_LEFT,
    )
    table_style = ParagraphStyle(
        "Table", fontName="Courier", fontSize=7.15, leading=8.7,
        textColor=colors.HexColor("#1E293B"), alignment=TA_CENTER,
    )

    story = [Paragraph("TP3 - Pergunta de classificação de intenção", title_style)]
    intro = section_body(source, "# TP3 — pergunta de classificação de intenção", "## Dados e distribuição das classes")
    for piece in paragraphs(intro):
        story.append(Paragraph(inline_markdown(piece), body_style))

    story.append(Paragraph("Dados e distribuição das classes", heading_style))
    distribution = section_body(source, "## Dados e distribuição das classes", "## Por que aprendizado supervisionado, não regressão linear")
    distribution_intro = distribution.split("| Intenção (n)", 1)[0]
    for piece in paragraphs(distribution_intro):
        story.append(Paragraph(inline_markdown(piece), body_style))
    cells = []
    for index in range(0, 46, 3):
        cells.append([
            Paragraph(f"{name} ({count})", table_style)
            for name, count in table_rows[index:index + 3]
        ] + [""] * max(0, 3 - len(table_rows[index:index + 3])))
    table = Table(cells, colWidths=[58 * mm] * 3, hAlign="CENTER", rowHeights=7 * mm)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.extend([Spacer(1, 3 * mm), table])

    story.append(Paragraph("Por que aprendizado supervisionado", heading_style))
    rationale = section_body(source, "## Por que aprendizado supervisionado, não regressão linear", "## Limite da validação externa")
    for piece in paragraphs(rationale):
        story.append(Paragraph(inline_markdown(piece), body_style))

    story.append(Paragraph("Limite da validação externa", heading_style))
    limits = section_body(source, "## Limite da validação externa", None)
    for piece in paragraphs(limits):
        if piece.startswith("Fontes:"):
            story.append(Paragraph(
                "Fontes: <link href='https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset'>Bitext Retail eCommerce</link>, "
                "<link href='https://github.com/americanas-tech/b2w-reviews01'>B2W-Reviews01</link> "
                "e relatório de validação PT-BR do projeto.",
                body_style,
            ))
        else:
            story.append(Paragraph(inline_markdown(piece), body_style))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(args.output), pagesize=A4, leftMargin=18 * mm,
        rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=21 * mm,
        title="TP3 - Pergunta de classificação de intenção",
        author="Nathalia Calazans Artigas e Daniel Augusto da Silva",
    )
    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"PDF criado: {args.output}")


if __name__ == "__main__":
    main()
