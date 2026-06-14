"""
PDF Report Generator for CodeAlpha Enterprise AI Platform.

Generates a full multi-section PDF experiment report using ReportLab,
including branded title page, TOC, tables, embedded SHAP images, and
an AI insights section.
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------

_PRIMARY = colors.HexColor("#4F46E5")    # Indigo 600
_SECONDARY = colors.HexColor("#7C3AED")  # Violet 600
_ACCENT = colors.HexColor("#06B6D4")     # Cyan 500
_TEXT_DARK = colors.HexColor("#1E1B4B")
_LIGHT_BG = colors.HexColor("#EEF2FF")  # Indigo 50
_HEADER_BG = colors.HexColor("#312E81")  # Indigo 900
_ALT_ROW = colors.HexColor("#F5F3FF")   # Violet 50

PAGE_W, PAGE_H = A4


def _make_styles() -> dict[str, ParagraphStyle]:
    """Build custom paragraph styles for the CodeAlpha report."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "CATitle",
            parent=base["Title"],
            fontSize=28,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "CASubtitle",
            fontSize=14,
            textColor=colors.HexColor("#C7D2FE"),
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName="Helvetica",
        ),
        "h1": ParagraphStyle(
            "CAH1",
            fontSize=16,
            textColor=_PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
            borderPad=4,
        ),
        "h2": ParagraphStyle(
            "CAH2",
            fontSize=13,
            textColor=_SECONDARY,
            spaceBefore=10,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "CABody",
            fontSize=10,
            textColor=_TEXT_DARK,
            spaceBefore=2,
            spaceAfter=4,
            leading=14,
            fontName="Helvetica",
        ),
        "bullet": ParagraphStyle(
            "CABullet",
            fontSize=10,
            textColor=_TEXT_DARK,
            leftIndent=14,
            spaceAfter=2,
            bulletIndent=6,
            leading=13,
            fontName="Helvetica",
        ),
        "code": ParagraphStyle(
            "CACode",
            fontSize=9,
            textColor=colors.HexColor("#065F46"),
            fontName="Courier",
            backColor=colors.HexColor("#ECFDF5"),
            borderPad=4,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "toc": ParagraphStyle(
            "CATOC",
            fontSize=11,
            textColor=_PRIMARY,
            spaceAfter=3,
            fontName="Helvetica",
        ),
        "caption": ParagraphStyle(
            "CACaption",
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName="Helvetica-Oblique",
        ),
    }


def _metrics_table_style() -> TableStyle:
    """Styled table for model metrics comparison."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D2FE")),
        ("BOX", (0, 0), (-1, -1), 1, _PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def _leaderboard_table_style() -> TableStyle:
    """Styled table for leaderboard ranking."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_BG]),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A5B4FC")),
        ("BOX", (0, 0), (-1, -1), 1, _PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        # Gold for rank 1
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FEF9C3")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
    ])


def _decode_shap_image(b64_str: str) -> RLImage | None:
    """Decode a base64 PNG string to a ReportLab Image."""
    try:
        raw = base64.b64decode(b64_str)
        buf = BytesIO(raw)
        img = RLImage(buf, width=5.5 * inch, height=3.2 * inch)
        return img
    except Exception as exc:
        logger.warning("Failed to decode SHAP image: %s", exc)
        return None


class PDFReportGenerator:
    """
    Generates a professional multi-section PDF experiment report.

    Usage::

        gen = PDFReportGenerator()
        path = gen.generate(
            output_path=Path("/reports/exp_42.pdf"),
            title="Fraud Detection Experiment #42",
            ...
        )
    """

    def generate(
        self,
        output_path: Path,
        title: str,
        task_type: str,
        dataset_summary: dict[str, Any],
        preprocessing_steps: list[str],
        model_architectures: dict[str, Any],
        metrics_table: list[dict[str, Any]],
        leaderboard: list[dict[str, Any]],
        shap_images: dict[str, str],      # {model_name: base64_png}
        ai_insights: str,
        recommendations: list[str],
    ) -> Path:
        """
        Build and write the complete PDF report.

        Args:
            output_path:         Destination ``.pdf`` file path.
            title:               Report title string.
            task_type:           ML task type (classification / regression / …).
            dataset_summary:     Dict with dataset metadata (rows, cols, target, …).
            preprocessing_steps: Ordered list of preprocessing step descriptions.
            model_architectures: Dict mapping model names to architecture descriptions.
            metrics_table:       List of per-model metric dicts.
            leaderboard:         Ranked list of model entries.
            shap_images:         Base64-encoded SHAP PNG images per model.
            ai_insights:         AI-generated insight text (Markdown-ish).
            recommendations:     List of action recommendation strings.

        Returns:
            The ``output_path`` after writing.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        styles = _make_styles()
        story: list = []

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=0.85 * inch,
            rightMargin=0.85 * inch,
            topMargin=0.9 * inch,
            bottomMargin=0.9 * inch,
            title=title,
            author="CodeAlpha Enterprise AI Platform",
        )

        # ----------------------------------------------------------------
        # Title page
        # ----------------------------------------------------------------
        story.extend(self._build_title_page(title, task_type, styles))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # Table of contents
        # ----------------------------------------------------------------
        story.append(Paragraph("Table of Contents", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.15 * inch))
        toc_items = [
            ("1. Executive Summary", "exec_summary"),
            ("2. Dataset Overview", "dataset"),
            ("3. Preprocessing Pipeline", "preprocessing"),
            ("4. Model Architectures", "architectures"),
            ("5. Performance Metrics", "metrics"),
            ("6. Leaderboard", "leaderboard"),
            ("7. Explainability (SHAP)", "shap"),
            ("8. AI Insights", "insights"),
            ("9. Recommendations", "recommendations"),
            ("10. Future Work", "future_work"),
        ]
        for text, _ in toc_items:
            story.append(Paragraph(f"• {text}", styles["toc"]))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 1. Executive Summary
        # ----------------------------------------------------------------
        story.append(Paragraph("1. Executive Summary", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))

        best_model = leaderboard[0] if leaderboard else {}
        best_model_name = best_model.get("model_name", best_model.get("model", "N/A"))
        best_score = best_model.get("accuracy", best_model.get("weighted_score", "N/A"))

        exec_lines = [
            f"This report presents a comprehensive evaluation of <b>{len(metrics_table)}</b> "
            f"machine learning models for a <b>{task_type}</b> task.",
            f"The top-performing model is <b>{best_model_name}</b> with an accuracy / "
            f"score of <b>{best_score}</b>.",
            f"The dataset contains <b>{dataset_summary.get('total_rows', 'N/A')}</b> samples "
            f"and <b>{dataset_summary.get('total_cols', 'N/A')}</b> features.",
            "All models were trained, evaluated, and ranked using the CodeAlpha "
            "automated ML pipeline with SHAP-based explainability.",
        ]
        for line in exec_lines:
            story.append(Paragraph(line, styles["body"]))
            story.append(Spacer(1, 0.05 * inch))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 2. Dataset Overview
        # ----------------------------------------------------------------
        story.append(Paragraph("2. Dataset Overview", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))

        ds_data = [["Property", "Value"]]
        for key, val in dataset_summary.items():
            label = key.replace("_", " ").title()
            ds_data.append([label, str(val)])

        if len(ds_data) > 1:
            ds_table = Table(ds_data, colWidths=[2.5 * inch, 4.0 * inch])
            ds_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D2FE")),
                ("BOX", (0, 0), (-1, -1), 1, _PRIMARY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(ds_table)
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 3. Preprocessing Pipeline
        # ----------------------------------------------------------------
        story.append(Paragraph("3. Preprocessing Pipeline", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                "The following preprocessing steps were applied to the raw dataset "
                "before model training:",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))
        for i, step in enumerate(preprocessing_steps, start=1):
            story.append(Paragraph(f"<b>Step {i}:</b> {step}", styles["bullet"]))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 4. Model Architectures
        # ----------------------------------------------------------------
        story.append(Paragraph("4. Model Architectures", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))

        arch_data = [["Model", "Architecture / Description"]]
        for model_name, desc in model_architectures.items():
            arch_data.append([model_name, str(desc)])

        if len(arch_data) > 1:
            arch_table = Table(arch_data, colWidths=[2.2 * inch, 4.3 * inch])
            arch_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _SECONDARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDD6FE")),
                ("BOX", (0, 0), (-1, -1), 1, _SECONDARY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(arch_table)
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 5. Performance Metrics
        # ----------------------------------------------------------------
        story.append(Paragraph("5. Performance Metrics", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))

        if metrics_table:
            all_keys: list[str] = []
            seen: set[str] = set()
            for row in metrics_table:
                for k in row:
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)

            preferred_order = ["model", "model_name", "accuracy", "precision",
                               "recall", "f1_score", "f1", "roc_auc",
                               "mse", "rmse", "mae", "r2",
                               "inference_ms", "training_sec"]
            ordered_keys: list[str] = []
            for pk in preferred_order:
                if pk in seen:
                    ordered_keys.append(pk)
            for k in all_keys:
                if k not in ordered_keys:
                    ordered_keys.append(k)

            header = [k.replace("_", "\n").title() for k in ordered_keys]
            m_data = [header]
            for row in metrics_table:
                r: list[str] = []
                for k in ordered_keys:
                    val = row.get(k, "—")
                    if isinstance(val, float):
                        r.append(f"{val:.4f}")
                    else:
                        r.append(str(val))
                m_data.append(r)

            col_w = min(1.1 * inch, 6.5 * inch / max(len(ordered_keys), 1))
            m_table = Table(m_data, colWidths=[col_w] * len(ordered_keys))
            m_table.setStyle(_metrics_table_style())
            story.append(m_table)
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 6. Leaderboard
        # ----------------------------------------------------------------
        story.append(Paragraph("6. Leaderboard", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                "Models are ranked by a weighted composite score: "
                "Accuracy×0.4 + Precision×0.2 + Recall×0.2 + "
                "(1/inference_ms)×0.1 + (1/training_sec)×0.1",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        if leaderboard:
            lb_keys = list(leaderboard[0].keys())
            lb_header = [k.replace("_", "\n").title() for k in lb_keys]
            lb_data = [lb_header]
            for entry in leaderboard:
                row = []
                for k in lb_keys:
                    val = entry.get(k, "—")
                    if isinstance(val, float):
                        row.append(f"{val:.4f}")
                    else:
                        row.append(str(val))
                lb_data.append(row)

            col_w = min(1.1 * inch, 6.5 * inch / max(len(lb_keys), 1))
            lb_table = Table(lb_data, colWidths=[col_w] * len(lb_keys))
            lb_table.setStyle(_leaderboard_table_style())
            story.append(lb_table)
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 7. SHAP Explainability
        # ----------------------------------------------------------------
        story.append(Paragraph("7. Explainability (SHAP)", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                "SHAP (SHapley Additive exPlanations) values show the contribution "
                "of each feature to individual predictions.  Positive values push "
                "predictions higher; negative values push them lower.",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        for model_name, b64_png in shap_images.items():
            story.append(Paragraph(f"Model: {model_name}", styles["h2"]))
            img = _decode_shap_image(b64_png)
            if img:
                story.append(img)
                story.append(
                    Paragraph(
                        f"Figure: SHAP summary plot for {model_name}.",
                        styles["caption"],
                    )
                )
            else:
                story.append(
                    Paragraph("[SHAP image unavailable]", styles["body"])
                )
            story.append(Spacer(1, 0.15 * inch))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 8. AI Insights
        # ----------------------------------------------------------------
        story.append(Paragraph("8. AI Insights", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                "The following insights were generated by the CodeAlpha AI assistant "
                "using Retrieval-Augmented Generation (RAG) over your experiment history:",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        for line in ai_insights.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.05 * inch))
            elif line.startswith("•") or line.startswith("-"):
                story.append(Paragraph(line, styles["bullet"]))
            elif line.startswith("**") and line.endswith("**"):
                story.append(Paragraph(f"<b>{line.strip('*')}</b>", styles["h2"]))
            else:
                story.append(Paragraph(line, styles["body"]))
        story.append(PageBreak())

        # ----------------------------------------------------------------
        # 9. Recommendations
        # ----------------------------------------------------------------
        story.append(Paragraph("9. Recommendations", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))
        for i, rec in enumerate(recommendations, start=1):
            story.append(Paragraph(f"<b>{i}.</b> {rec}", styles["bullet"]))
            story.append(Spacer(1, 0.04 * inch))
        story.append(Spacer(1, 0.2 * inch))

        # ----------------------------------------------------------------
        # 10. Future Work
        # ----------------------------------------------------------------
        story.append(Paragraph("10. Future Work", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=_PRIMARY))
        story.append(Spacer(1, 0.1 * inch))

        future_items = [
            "Expand the dataset with additional labelled samples to improve generalisation.",
            "Explore ensemble stacking of the top-3 leaderboard models.",
            "Apply neural architecture search (NAS) for deep learning tasks.",
            "Implement online learning for continuous model retraining on production data.",
            "Add fairness metrics (demographic parity, equalised odds) for regulated domains.",
            "Profile memory and compute efficiency for edge deployment.",
        ]
        for item in future_items:
            story.append(Paragraph(f"• {item}", styles["bullet"]))

        # ----------------------------------------------------------------
        # Build PDF
        # ----------------------------------------------------------------
        doc.build(story, onFirstPage=self._page_header_footer, onLaterPages=self._page_header_footer)
        logger.info("PDF report written to %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Title page
    # ------------------------------------------------------------------

    def _build_title_page(
        self, title: str, task_type: str, styles: dict[str, ParagraphStyle]
    ) -> list:
        """Build the title page flowables."""
        from reportlab.platypus import KeepTogether

        items: list = [
            Spacer(1, 1.2 * inch),
            Paragraph("CodeAlpha", styles["title"]),
            Paragraph("Enterprise AI Platform", styles["subtitle"]),
            Spacer(1, 0.3 * inch),
            HRFlowable(width="80%", thickness=2, color=_ACCENT),
            Spacer(1, 0.3 * inch),
            Paragraph(title, styles["h1"]),
            Spacer(1, 0.2 * inch),
            Paragraph(f"Task Type: {task_type.title()}", styles["subtitle"]),
            Spacer(1, 0.15 * inch),
            Paragraph(
                "Automated ML Experiment Report",
                ParagraphStyle(
                    "label",
                    fontSize=11,
                    textColor=colors.HexColor("#6D28D9"),
                    alignment=TA_CENTER,
                ),
            ),
            Spacer(1, 2.5 * inch),
            HRFlowable(width="60%", thickness=1, color=_ACCENT),
            Spacer(1, 0.15 * inch),
            Paragraph(
                "Generated by CodeAlpha AutoML Pipeline",
                ParagraphStyle("footer", fontSize=9, textColor=colors.grey, alignment=TA_CENTER),
            ),
        ]
        return items

    # ------------------------------------------------------------------
    # Page header / footer callback
    # ------------------------------------------------------------------

    @staticmethod
    def _page_header_footer(canvas, doc):
        """Draw header and footer on every page."""
        canvas.saveState()
        page_w, page_h = A4

        # Header stripe
        canvas.setFillColor(_PRIMARY)
        canvas.rect(0, page_h - 0.45 * inch, page_w, 0.45 * inch, fill=True, stroke=False)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.white)
        canvas.drawString(0.85 * inch, page_h - 0.30 * inch, "CodeAlpha Enterprise AI Platform")

        # Footer
        canvas.setFillColor(_TEXT_DARK)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            0.85 * inch, 0.45 * inch, "Confidential — Generated by CodeAlpha AutoML"
        )
        canvas.drawRightString(
            page_w - 0.85 * inch,
            0.45 * inch,
            f"Page {doc.page}",
        )
        canvas.setStrokeColor(_PRIMARY)
        canvas.setLineWidth(0.5)
        canvas.line(0.85 * inch, 0.60 * inch, page_w - 0.85 * inch, 0.60 * inch)
        canvas.restoreState()
