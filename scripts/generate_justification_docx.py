import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from scripts.config import REPORTS_DIR

def add_styled_heading(doc: Document, text: str, level: int = 1, size: int = 16):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(size)
    run.bold = True
    return h

def create_justification_document():
    doc = Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Style: Set base font to Arial/Calibri
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("FCA Consumer Duty Outcome Monitoring")
    title_run.bold = True
    title_run.font.size = Pt(22)
    title_run.font.name = 'Calibri'
    
    # Subtitle
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle.add_run("Project Justification and Business Case")
    sub_run.italic = True
    sub_run.font.size = Pt(14)
    sub_run.font.name = 'Calibri'

    doc.add_paragraph("\n") # spacing

    # Section 1: Executive Summary
    add_styled_heading(doc, "1. Executive Summary")

    p1 = doc.add_paragraph(
        "This project implements an automated, data-driven framework for monitoring customer outcomes "
        "under the Financial Conduct Authority (FCA) Consumer Duty regulations (PS22/9). By building "
        "reproducible analytical pipelines, we demonstrate how financial services firms can transition "
        "from traditional checklist compliance to proactive risk monitoring. This system helps protect "
        "vulnerable customers, ensures products deliver fair value, and optimizes customer support channels."
    )

    # Section 2: Core Business Justifications
    add_styled_heading(doc, "2. Core Business Justifications")

    # Bullet 1
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Showcases High-Value Domain Expertise: ")
    r.bold = True
    p.add_run(
        "The FCA Consumer Duty regulation represents the most significant regulatory shift in UK retail "
        "financial services in a decade. Developing this system shows direct technical and regulatory "
        "competency in conduct risk, product governance, and customer outcomes reporting."
    )

    # Bullet 2
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Proactive Detriment Prevention: ")
    r.bold = True
    p.add_run(
        "Instead of waiting for customer complaints to escalate to the Financial Ombudsman Service (FOS), "
        "this system aggregates data across siloed transactional, operations, and complaints tables to "
        "proactively spot service barriers, pricing anomalies, and unfair outcomes before they result in regulatory penalties."
    )

    # Bullet 3
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Privacy-Preserving Analytics & Benchmarking: ")
    r.bold = True
    p.add_run(
        "Actual customer data contains sensitive Personal Identifiable Information (PII) and special category "
        "vulnerability markers. This project demonstrates a methodology for calibrating synthetic customer portfolios "
        "against real, anonymised UK public datasets (FCA, FOS, and ONS), enabling risk committees to perform robust "
        "testing without exposing sensitive customer data."
    )

    # Section 3: The Four Outcome Pillars
    add_styled_heading(doc, "3. Alignment with FCA Outcome Pillars")

    # Subheadings for outcomes
    for outcome_title, desc in [
        ("Products & Services", "Ensuring products are designed to meet the needs of a specified target market and distributed via appropriate channels."),
        ("Price & Value", "Verifying that prices represent fair value relative to the benefits received, benchmarked against FCA general insurance value measures."),
        ("Consumer Support", "Removing systemic friction and administrative delays that prevent retail customers from fully utilizing their products."),
        ("Consumer Understanding", "Ensuring communications are clear, transparent, and do not mislead vulnerable or retail segments.")
    ]:
        p = doc.add_paragraph()
        r = p.add_run(f"•  {outcome_title}: ")
        r.bold = True
        p.add_run(desc)

    # Section 4: Data Sources and Provenance
    add_styled_heading(doc, "4. Data Sources and Calibration")

    doc.add_paragraph(
        "To ensure compliance with data quality standards, the analytical model relies on public datasets "
        "from UK regulatory bodies:"
    )

    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("FCA Firm-Level Complaints Data: ")
    r.bold = True
    p.add_run("Establishes the industry baseline for uphold rates and complaint closure speed.")

    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("FCA GI Value Measures: ")
    r.bold = True
    p.add_run("Provides product-level claims ratios and claim acceptance rates for fair value assessments.")

    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("ONS Population Estimates: ")
    r.bold = True
    p.add_run("Used to model geographic and demographic distribution of vulnerable consumer cohorts.")

    # Save document
    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, "project_justification.docx")
    doc.save(output_path)
    print(f"[SUCCESS] Saved document to {output_path}")

if __name__ == "__main__":
    create_justification_document()

