"""
Export script for FDIC Bank Failure Early-Warning System Academic Report.
Generates: deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx
Fully aligned with the Professor's 100-Point Marking Rubric.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# Palette
NAVY = RGBColor(27, 54, 93)         # #1B365D - Deep Academic Navy
SLATE = RGBColor(52, 73, 94)        # #34495E - Dark Slate
CHARCOAL = RGBColor(33, 37, 41)     # #212529 - Body Text
GRAY_TEXT = RGBColor(108, 117, 125) # #6C757D - Muted Gray
WHITE = RGBColor(255, 255, 255)

NAVY_HEX = "1B365D"
LIGHT_BG_HEX = "F4F6F9"
BORDER_HEX = "D3D3D3"
ALT_ROW_HEX = "F8F9FA"


def set_cell_background(cell, fill_hex: str) -> None:
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top: int = 70, bottom: int = 70, left: int = 100, right: int = 100) -> None:
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)


def set_table_borders(table, border_color: str = BORDER_HEX) -> None:
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="{NAVY_HEX}"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{NAVY_HEX}"/>
                <w:left w:val="none"/>
                <w:right w:val="none"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)


def format_table_rows(table) -> None:
    for row_idx, row in enumerate(table.rows):
        trPr = row._element.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if row_idx == 0:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))


def add_heading_1(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph(style='Heading 1')
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.text = text
    run = p.runs[0]
    run.font.name = "Times New Roman"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = NAVY


def add_heading_2(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph(style='Heading 2')
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.text = text
    run = p.runs[0]
    run.font.name = "Times New Roman"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = NAVY


def add_heading_3(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph(style='Heading 3')
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.text = text
    run = p.runs[0]
    run.font.name = "Times New Roman"
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.color.rgb = SLATE


def add_paragraph(doc: docx.Document, text: str, bold_prefix: str = "", space_after: Pt = Pt(3.5)) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = space_after
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = NAVY
    r_text = p.add_run(text)
    r_text.font.name = "Times New Roman"
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = CHARCOAL


def add_callout(doc: docx.Document, text: str, title: str = "") -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, LIGHT_BG_HEX)
    set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="{NAVY_HEX}"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if title:
        rt = p.add_run(f"{title}\n")
        rt.font.name = "Times New Roman"
        rt.font.size = Pt(9.5)
        rt.font.bold = True
        rt.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = CHARCOAL
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_figure(doc: docx.Document, img_path: Path | str, caption: str, width: Inches = Inches(6.2)) -> None:
    img_path = Path(img_path)
    if not img_path.exists():
        add_paragraph(doc, f"[Figure Missing: {img_path.name}]", bold_prefix="Warning: ")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(img_path), width=width)

    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(6)
    c_run = cp.add_run(caption)
    c_run.font.name = "Times New Roman"
    c_run.font.size = Pt(8.5)
    c_run.font.italic = True
    c_run.font.color.rgb = GRAY_TEXT


def add_styled_table(
    doc: docx.Document,
    headers: list[str],
    data_rows: list[list[str]],
    col_widths: list[float] | None = None,
    caption: str | None = None,
    alignments: list[WD_ALIGN_PARAGRAPH] | None = None
) -> None:
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(5)
        cp.paragraph_format.space_after = Pt(2)
        cp.paragraph_format.keep_with_next = True
        c_run = cp.add_run(caption)
        c_run.font.name = "Times New Roman"
        c_run.font.size = Pt(8.5)
        c_run.font.bold = True
        c_run.font.color.rgb = NAVY

    tbl = doc.add_table(rows=len(data_rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    hdr_row = tbl.rows[0]
    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx]
        set_cell_background(cell, NAVY_HEX)
        set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.alignment = alignments[idx] if alignments else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = WHITE

    for r_idx, row_vals in enumerate(data_rows):
        row = tbl.rows[r_idx + 1]
        bg_col = ALT_ROW_HEX if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            if bg_col != "FFFFFF":
                set_cell_background(cell, bg_col)
            set_cell_margins(cell, top=45, bottom=45, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.alignment = alignments[c_idx] if alignments else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(val))
            r.font.name = "Times New Roman"
            r.font.size = Pt(8)
            r.font.color.rgb = CHARCOAL

    format_table_rows(tbl)
    if col_widths:
        for row in tbl.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def verify_figures(figures_dir: Path) -> dict[str, str]:
    manifest_path = Path("docs/evidence/verified_figures_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    expected_hashes = manifest["figures_sha256"]

    verified = {}
    for fname, exp_hash in expected_hashes.items():
        fpath = figures_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Required figure {fname} not found in {figures_dir}")
        with open(fpath, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
        if actual_hash != exp_hash.lower():
            raise ValueError(f"Figure {fname} hash mismatch: {actual_hash} != {exp_hash}")
        verified[fname] = actual_hash
    return verified


def build_submission_document() -> Path:
    figures_dir = Path("docs/figures")
    verified_hashes = verify_figures(figures_dir)
    print(f"Verified {len(verified_hashes)} official figures via SHA-256.")

    doc = docx.Document()

    # Page setup - A4 with 1-inch margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # ---------------------------------------------------------------------------
    # COVER PAGE
    # ---------------------------------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(8)
    p_inst.paragraph_format.space_after = Pt(2)
    r = p_inst.add_run("NATIONAL ECONOMICS UNIVERSITY\nSCHOOL OF BANKING AND FINANCE")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY

    p_prog = doc.add_paragraph()
    p_prog.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_prog.paragraph_format.space_before = Pt(2)
    p_prog.paragraph_format.space_after = Pt(14)
    r = p_prog.add_run("BACHELOR OF FINANCIAL TECHNOLOGY (CLASS BFT65B)\nCOURSE: BIG DATA ANALYTICS IN FINANCE")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = SLATE

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(4)
    r = p_title.add_run("U.S. BANK FAILURE EARLY-WARNING SYSTEM")
    r.font.name = "Times New Roman"
    r.font.size = Pt(17)
    r.font.bold = True
    r.font.color.rgb = NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    r = p_sub.add_run("A Point-in-Time Big Data Engineering, Multi-Engine Scalability, and Cost-Sensitive Predictive Framework (1984Q1–2026Q2)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10.5)
    r.font.italic = True
    r.font.color.rgb = CHARCOAL

    # Student metadata box
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_rows = [
        ("Student Full Name:", "Dao Huy Thanh Vinh"),
        ("Student ID (MSV):", "11231024"),
        ("Academic Program & Cohort:", "Bachelor of Financial Technology (BFT65B — 95% English-Taught Program)"),
        ("Course & Academic Unit:", "Big Data Analytics in Finance — School of Banking and Finance, NEU"),
        ("Public GitHub Repository:", "https://github.com/vinhong0506-coder/fdic-bank-risk-research (branch main)")
    ]
    for idx, (label, val) in enumerate(meta_rows):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = Inches(2.2), Inches(4.3)
        set_cell_background(c0, LIGHT_BG_HEX)
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 35, 35, 60, 60)
        set_cell_margins(c1, 35, 35, 60, 60)

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(8.5)
        r0.font.bold = True
        r0.font.color.rgb = NAVY

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = CHARCOAL

    format_table_rows(meta_table)
    set_table_borders(meta_table)

    add_paragraph(doc, "", space_after=Pt(3))

    # Mandatory First-Page Evidence Table (Locked Dataset Snapshot)
    headers_c1 = ["Partition Horizon", "Calendar Scope", "Total Records", "Valid Labeled Obs", "Positive Bank-Qs (y=1)", "Distinct Failed Banks", "Supervisory & Ingestion Status"]
    data_c1 = [
        ["Raw Bulk Ingestion", "1984Q1–2026Q2", "1,682,738", "N/A", "N/A", "3,585 (Registry)", "170 Qtrs Downloaded 2026-11-23"],
        ["Clean PIT Panel", "1984Q1–2026Q2", "1,677,107", "N/A", "N/A", "3,241 (Matched)", "5,631 Zombie Rows Purged"],
        ["Development Split", "1984Q1–2007Q4", "1,224,942", "1,176,223", "10,153 (0.863%)", "2,680 Unique Charters", "Model Fitting & Expanding CV"],
        ["Embargo Gap", "2008Q1–2008Q4", "33,966", "33,039", "402 (1.217%)", "176 Unique Charters", "4-Quarter Purge / Zero Leakage"],
        ["Out-of-Time Test", "2009Q1–2025Q2", "400,698", "386,964", "1,775 (0.459%)", "500 Unique Charters", "Strict One-Time Evaluation"],
        ["Terminal Horizon", "2025Q3–2026Q2", "17,501", "0 (Censored)", "N/A", "N/A", "Unexpired Forward Target Window"]
    ]
    add_styled_table(
        doc,
        headers=headers_c1,
        data_rows=data_c1,
        col_widths=[1.1, 1.0, 0.8, 0.9, 0.9, 1.0, 1.1],
        caption="Table C.1: Mandatory First-Page Empirical Dataset Snapshot, Partition Architecture, and Entity Accounting Audit",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_date.paragraph_format.space_before = Pt(4)
    p_date.paragraph_format.space_after = Pt(0)
    r = p_date.add_run("Submission Date: November 26, 2026 | National Economics University, Hanoi, Vietnam")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True
    r.font.color.rgb = SLATE

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # TABLE OF CONTENTS
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "TABLE OF CONTENTS")

    toc_items = [
        ("Executive Summary and Core Research Inquiries", "3"),
        ("Part 1 – Acquisition & Storage Engineering [15 Points]", "4"),
        ("  1.1 Reproducible Data Acquisition and Ingestion Architecture", "4"),
        ("  1.2 Three-Tier Verification and Integrity Audit", "5"),
        ("  1.3 Columnar Storage Engineering and Empirical Benchmarks", "5"),
        ("  1.4 Design Decisions and Storage Justification", "6"),
        ("Part 2 – Data Quality & Bank-Quarter Panel Construction [20 Points]", "7"),
        ("  2.1 Automated Data-Quality Framework and Defect Detection Rules", "7"),
        ("  2.2 Bank Lifecycle and Event Classification Taxonomy", "8"),
        ("  2.3 Point-in-Time Panel Construction and Temporal Splitting", "9"),
        ("  2.4 Regulatory Capital Structural Zero Reporting Audit", "10"),
        ("Part 3 – Scalable Processing Engine Benchmark [25 Points]", "11"),
        ("  3.1 Polars Lazy API Implementation and Optimization Plan", "11"),
        ("  3.2 Eager pandas Baseline and Memory Overhead", "12"),
        ("  3.3 Distributed PySpark Local[*] and Catalyst Plan Execution", "12"),
        ("  3.4 Cross-Engine Numeric Equivalence Verification", "13"),
        ("  3.5 Multi-Scale Empirical Performance Benchmark (27 Measured Runs)", "13"),
        ("  3.6 Distributed Cluster Break-Even and Hardware Justification Boundary", "15"),
        ("Part 4 – Point-in-Time Feature Engineering Pipeline [15 Points]", "16"),
        ("  4.1 CAMELS Feature Selection and Financial Interpretability", "16"),
        ("  4.2 Anti-Leakage Feature Construction and Calendar Indexing", "17"),
        ("  4.3 Train-Only Preprocessing Pipeline and Invariance Testing", "18"),
        ("Part 5 – Predictive Modeling & Empirical Validation [15 Points]", "19"),
        ("  5.1 Model Selection Rationales and Baseline Algorithms", "19"),
        ("  5.2 Expanding Window Cross-Validation Architecture", "19"),
        ("  5.3 Highly Imbalanced Metric Evaluation and Out-of-Time Test Results", "20"),
        ("  5.4 Asymmetric Supervisory Loss and Cost-Sensitive Alarm Thresholding", "21"),
        ("  5.5 Macroeconomic Regime Sensitivity and Failure Non-Additivity", "22"),
        ("Part 6 – Conclusions, Research Questions & Policy Implications [5 Points]", "23"),
        ("  6.1 Explicit Direct Answers to the Professor's Three Research Questions", "23"),
        ("  6.2 Comprehensive Systemic Limitations and Governance Principles", "24"),
        ("  6.3 Policy and Architectural Adaptation to the State Bank of Vietnam (SBV)", "25"),
        ("  6.4 Academic Integrity, Code Citation, and Generative AI Disclosure", "26"),
        ("Academic & Regulatory References", "27"),
        ("Technical Appendices (Appendices A to E)", "28"),
        ("  Appendix A: Regulatory Capital Accounting Transition (Basel I to CBLR)", "28"),
        ("  Appendix B: Multi-Engine Technical Specifications and Environment Topology", "29"),
        ("  Appendix C: Mathematical Formulation of 30 Point-in-Time CAMELS Features", "30"),
        ("  Appendix D: Time-Series Expanding Cross-Validation Partition Dates", "31"),
        ("  Appendix E: Machine Learning Hyperparameter Grids and Tuning Protocols", "31")
    ]

    for title, pg in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.15
        is_sub = title.startswith("  ")
        r_t = p.add_run(title)
        r_t.font.name = "Times New Roman"
        r_t.font.size = Pt(8.5) if is_sub else Pt(9.5)
        r_t.font.bold = not is_sub
        r_t.font.color.rgb = SLATE if is_sub else NAVY

        # Leader dots
        dots_len = max(2, (80 - len(title)))
        leader = " " + "." * dots_len + " "
        r_l = p.add_run(leader)
        r_l.font.name = "Times New Roman"
        r_l.font.size = Pt(8.5)
        r_l.font.color.rgb = GRAY_TEXT

        r_p = p.add_run(pg)
        r_p.font.name = "Times New Roman"
        r_p.font.size = Pt(8.5) if is_sub else Pt(9.5)
        r_p.font.bold = True
        r_p.font.color.rgb = CHARCOAL

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # EXECUTIVE SUMMARY & RESEARCH QUESTIONS
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "EXECUTIVE SUMMARY AND CORE RESEARCH INQUIRIES")

    add_paragraph(
        doc,
        "Commercial banking stability is an essential prerequisite for sustainable macroeconomic growth and systemic financial resilience. When banking institutions become insolvent, the resulting externalities—including the erosion of depositor confidence, the sudden contraction of credit intermediation, and the depletion of sovereign deposit insurance reserves—inflict severe social and fiscal costs. To mitigate these risks, regulatory and supervisory authorities deploy automated Early-Warning Systems (EWS) to continuously monitor the risk profile of commercial banks, identify emerging financial fragilities, and prioritize institutions for targeted on-site examinations. This empirical research investigates the end-to-end data engineering, multi-engine computational scalability, and econometrically defensible predictive modeling of bank failure using the complete historical universe of Federal Deposit Insurance Corporation (FDIC) Call Reports across 170 consecutive quarters from 1984Q1 through 2026Q2 (1.68 million bank-quarters).",
        bold_prefix="Supervisory Motivation: "
    )
    add_paragraph(
        doc,
        "Unlike academic prototypes that rely on cross-sectional snapshots, synthetic toy datasets, or balanced panels that introduce fatal survivor bias, this project directly confronts real-world financial Big Data challenges. These include massive historical schema drift across four decades, profound regulatory regime shifts (such as the enactment of the Basel I Accord in 1990 and the introduction of the Community Bank Leverage Ratio in 2020), extreme class imbalance where failures represent less than 0.5% of quarterly observations, post-failure receivership filings ('zombie rows'), and highly asymmetric operational loss functions. By combining modern vectorized columnar execution engines (Polars Lazy API) and distributed cluster architectures (Apache Spark / PySpark) with an anti-leakage Point-in-Time (PIT) feature store, this report addresses three foundational research inquiries established in the course specification:",
        bold_prefix="Big Data Research Scope: "
    )

    add_callout(
        doc,
        "Question 1 (Storage & Processing Scale): How should four decades of bank reports be stored and processed on a laptop, and when would a Spark cluster be needed?\n\n"
        "Question 2 (Raw Data Quality & Anti-Leakage Assurance): What quality problems do the raw data contain, and how does the pipeline handle them without look-ahead bias?\n\n"
        "Question 3 (Early-Warning Defensibility & Supervisory Utility): Can the pipeline's output support an honestly validated early-warning model?",
        title="EXACT RESEARCH INQUIRIES FROM ASSIGNMENT SPECIFICATION (Q1, Q2, Q3)"
    )

    add_paragraph(
        doc,
        "Key Empirical Findings:\n"
        "1. Storage Engineering: Parquet format with Zstandard (zstd) compression compresses 424.1 MiB of raw CSV Call Reports to 143.9 MiB (a 2.95x physical compression ratio) while accelerating full-table scan query latency by 21.82x (0.47s vs. 10.26s).\n"
        "2. Compute Scalability (Q1): On single-node multi-core hardware, Polars Lazy API executes a representative seven-feature financial analytics workload across 1.68M rows in 0.797 seconds (2.10M rows/s), running 6.47x faster than pandas (5.157s) and 18.52x faster than PySpark Local[*] (14.757s). Across 27 executed experimental benchmark runs spanning 1x, 2x (3.35M rows), and 5x (8.39M rows), Polars maintains sub-3-second latency. PySpark Local[*] incurs substantial JVM startup, serialization, and Catalyst coordination overhead, confirming that distributed frameworks are inefficient on single-node hardware. A distributed Spark cluster is justified when working sets exceed available host physical RAM or when multi-node distributed storage requires network shuffling.\n"
        "3. Data Quality & Anti-Leakage (Q2): The pipeline systematically identifies and eliminates 5,631 post-closure zombie filings across 62 unique failure CERTs. Look-ahead bias is strictly prevented through four layers: an integer calendar quarter index (q_idx) preventing artificial lag shifts, a 1-year mandatory embargo quarantine (calendar year 2008: 33,039 valid observations, 176 unique failed banks) separating Development from Test, an explicit 4-quarter forward failure target window, and preprocessor transformations (Winsorization, median imputation, Z-score standardization) fitted strictly on Development data. The panel is structured as a report-date Point-in-Time (PIT) panel indexed by Call Report date (REPDTE), distinguishing accounting quarter boundaries from as-reported vintage filing archives.\n"
        "4. Model Defensibility & Supervisory Utility (Q3): Evaluated strictly ONCE on 386,964 held-out out-of-time bank-quarters (2009Q1–2025Q2; 1,775 positive bank-quarters, 500 unique failed bank charters), LightGBM calibrated under an empirical FDIC resolution loss ratio of 40.3:1 (median resolution loss = 20.17% of assets; assumed exam cost CFP = 0.50% of assets) at frozen threshold tau* = 0.0201 captures 484 out of 500 unique failed banks (96.8% institutional recall) and 93.30% of distressed quarters while flagging only 1.78% of eligible held-out Test bank-quarter observations (5,230 alerts), reducing modeled expected supervisory loss units by 59.7% relative to uncalibrated Logistic Regression under the assumed loss function.",
        bold_prefix="Summary of Core Findings: "
    )

    # ---------------------------------------------------------------------------
    # PART 1 – ACQUISITION & STORAGE [15 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 1 – ACQUISITION & STORAGE [15 POINTS]")

    add_heading_2(doc, "1.1 Reproducible Data Acquisition and Ingestion Architecture")
    add_paragraph(
        doc,
        "The primary data source for this study consists of the official Consolidated Reports of Condition and Income (Call Reports, FFIEC 031 for domestic and foreign offices, FFIEC 041 for domestic-only offices) disseminated by the Federal Deposit Insurance Corporation (FDIC). Every insured commercial bank and savings institution in the United States is legally mandated to submit quarterly financial filings. In the FDIC data warehouse, individual financial institutions are tracked by their unique Federal Certificate Number (CERT), and quarterly reporting periods are designated by the Report Date (REPDTE), corresponding to calendar quarter-end dates (March 31, June 30, September 30, and December 31).",
        bold_prefix="FDIC Reporting Universe: "
    )
    add_paragraph(
        doc,
        "The automated acquisition pipeline was implemented in src/fdic_pipeline/ingest.py. Rather than downloading ad-hoc bulk ZIP archives manually, the ingestion system programmatically interacts with the FDIC BankFind Suite REST API (financials endpoint: https://banks.data.fdic.gov/api/financials). The query parameters enforce strict quarterly temporal boundaries via filters=REPDTE:[YYYYMMDD TO YYYYMMDD], requesting 33 essential financial and structural attributes. To overcome the REST API's 10,000-record single-response ceiling, the ingestion engine implements offset pagination (limit=10000, offset=N). Network resilience is guaranteed via exponential backoff retry logic (up to 5 attempts per quarter with randomized jitter) and deterministic HTTP error handling (handling 429 rate limits and 5xx gateway timeouts). Resumability is built into the ingestion state machine: before issuing API calls for a given quarter, the engine checks local disk storage; if the quarterly partition exists and matches expected row counts, the network fetch is safely bypassed.",
        bold_prefix="API Ingestion Engineering: "
    )
    add_paragraph(
        doc,
        "The acquisition period covers exactly 170 continuous quarters from 1984Q1 through 2026Q2. The actual download was executed and cryptographically logged on November 23, 2026, between 11:38 and 12:05 Vietnam Time. Across all 170 quarters, exactly 1,682,738 raw financial observation rows were successfully retrieved without a single missing quarterly partition key.",
        bold_prefix="Temporal Coverage & Volume: "
    )

    add_heading_2(doc, "1.2 Three-Tier Ingestion Verification and Integrity Audit")
    add_paragraph(
        doc,
        "To ensure absolute scientific reproducibility and auditability, data engineering best practices require distinguishing three independent levels of verification, rather than assuming that file presence implies data integrity:",
        bold_prefix="Integrity Audit Framework: "
    )
    add_paragraph(
        doc,
        "Tier 1 (Manifest Existence & Count Parity): All 170 quarterly manifest entries exist in data_raw/fdic/manifest_financials.json. The sum of reported rows across all quarterly manifest partitions equals exactly 1,682,738 records, matching the total row count of the raw ingested dataset.\n"
        "Tier 2 (Saved Checksum & Completeness Flags): The pipeline audit script evaluated artifacts/stageB/audit/manifest_verification.csv across all 170 quarters. All quarters satisfy complete == True, file_exists == True, and sha_match == True relative to the manifest metadata created at download time.\n"
        "Tier 3 (Independent Source Recomputation Audit): In accordance with strict academic integrity standards, the Stage E technical audit (docs/evidence/part5_integrity_status.json) explicitly recorded that an independent full SHA-256 recalculation of all 170 raw source files directly against the original FDIC server responses was NOT independently conducted during Stage E; instead, the saved manifest verification flags were verified. This distinction is transparently disclosed: while local file integrity is confirmed by manifest flags, independent server-side bitwise verification remains a documented project boundary.",
        bold_prefix="Three Verification Tiers: "
    )

    add_heading_2(doc, "1.3 Columnar Storage Engineering and Empirical Benchmarks")
    add_paragraph(
        doc,
        "Financial Call Reports contain wide, sparse tables with mixed data types (integers, floating-point ratios, dates, and categorical strings). Storing four decades of longitudinal records in uncompressed, row-oriented text formats such as CSV is highly inefficient. Uncompressed CSV requires parsing ASCII text into binary representations upon every read, discards data type definitions, lacks dictionary encoding for repeated text fields, and forces analytical queries to scan every column on disk even when only a small subset is requested.",
        bold_prefix="Storage Architecture Dilemma: "
    )
    add_paragraph(
        doc,
        "The analytical storage layer was engineered using Apache Parquet, an open-source columnar storage format. Parquet organizes data into columnar chunks with dictionary encoding, run-length encoding (RLE), and bit-packing. Furthermore, Parquet files store rich file metadata (including column-level minimum and maximum statistics, dictionary page offsets, and schema definitions), enabling execution engines to perform projection pushdown (reading only the required columns) and predicate pushdown (skipping irrelevant row groups without reading raw bytes). To identify the optimal physical compression codec, an empirical storage benchmark was executed comparing uncompressed CSV against Parquet compressed with Snappy, Zstandard (zstd), and Brotli.",
        bold_prefix="Columnar Storage Optimization: "
    )

    # Table 1.1 Storage Benchmark
    headers_t1 = ["Storage Configuration", "Physical File Size", "Compression Ratio", "Write Latency", "Read Latency", "Relative Read Speedup", "Analytical Design Implication"]
    data_t1 = [
        ["Raw CSV (Uncompressed)", "424.1 MiB", "1.00x (Baseline)", "51.44 s", "10.26 s", "1.00x (Baseline)", "Prohibitive I/O tax; forces full-file text parsing"],
        ["Parquet (Snappy)", "172.4 MiB", "2.46x Reduction", "6.47 s", "1.06 s", "9.68x Faster", "Fast write speed; balanced for streaming ingestion"],
        ["Parquet (Zstandard - zstd)", "143.9 MiB", "2.95x Reduction", "4.07 s", "0.47 s", "21.82x Faster", "Optimal analytical layout; lowest size & fastest read"],
        ["Parquet (Brotli)", "144.9 MiB", "2.93x Reduction", "19.14 s", "0.56 s", "18.32x Faster", "High compression ratio but CPU-intensive write latency"]
    ]
    add_styled_table(
        doc,
        headers=headers_t1,
        data_rows=data_t1,
        col_widths=[1.5, 0.8, 0.9, 0.7, 0.7, 0.8, 1.1],
        caption="Table 1.1: Empirical Storage Footprint, Compression Efficiency, and Read/Write Latency (170 Quarters, 1.68M Rows)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_figure(
        doc,
        figures_dir / "fig1_storage_benchmark.png",
        "Figure 1: Empirical Storage Footprint and Read/Write Latency Benchmark (1984Q1–2026Q2, 170 Quarters, 1.68M Rows). Data labels: CSV 424.1 MiB, Snappy 172.4 MiB, Zstandard 143.9 MiB, Brotli 144.9 MiB. Read latencies: CSV 10.26s, Zstd 0.47s (21.82x speedup). Write latencies: CSV 51.44s, Zstd 4.07s."
    )

    add_heading_2(doc, "1.4 Design Decisions and Storage Justification")
    add_paragraph(
        doc,
        "As established in Table 1.1 and Figure 1, Parquet with Zstandard compression is the definitively superior storage configuration for bank failure modeling. Zstandard achieves the smallest footprint (143.9 MiB vs. 424.1 MiB for CSV, a 2.95x compression factor) and the fastest read throughput (0.47 seconds vs. 10.26 seconds, representing a 21.82x sequential read speedup). While Brotli achieves comparable compression (144.9 MiB), its write latency is nearly five times higher (19.14s vs. 4.07s). Alternative storage architectures, such as relational SQLite or PostgreSQL databases, were evaluated but rejected: relational row stores require substantial indexing overhead, consume 2–3x more physical disk space, and lack vectorized integration with modern columnar data frame libraries. Consequently, Parquet-zstd was selected as the locked baseline storage standard for the entire research pipeline.",
        bold_prefix="Storage Decision Rationale: "
    )

    # ---------------------------------------------------------------------------
    # PART 2 – DATA QUALITY & PANEL [20 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 2 – DATA QUALITY & BANK-QUARTER PANEL [20 POINTS]")

    add_heading_2(doc, "2.1 Automated Data-Quality Framework and Defect Detection Rules")
    add_paragraph(
        doc,
        "Empirical banking panels spanning 42.5 years are plagued by historical reporting anomalies, entity restructuring, and accounting discontinuities. An automated data-quality audit framework was constructed in src/fdic_pipeline/audit.py to execute exhaustive integrity checks across the raw ingested universe. Table 2.1 documents the taxonomy of defects, formal detection rules, observed extents, and methodological treatments applied.",
        bold_prefix="Quality Assurance Framework: "
    )

    # Table 2.1 Data Quality Audit
    headers_t21 = ["Data-Quality Defect", "Formal Detection Rule", "Observed Extent in Panel", "Methodological Treatment", "Analytical Reasoning & Impact"]
    data_t21 = [
        ["Missing / Invalid Bank ID", "pl.col('CERT').is_null() | (pl.col('CERT') <= 0)", "0 rows in Financials; 488 rows in Failures", "Excluded from active failure mapping", "CERT is the invariant FDIC entity primary key"],
        ["Duplicate Entity-Quarter Key", "df.group_by(['CERT', 'REPDTE']).len() > 1", "0 duplicate keys across 1.68M rows", "Validated invariant primary key", "Guarantees uniqueness of bank-quarter time steps"],
        ["Post-Exit Zombie Filings", "REPDTE > failure_date for failed CERTs", "5,631 bank-quarters (62 unique CERTs)", "Strictly purged from panel", "Receivership accounting distorts pre-failure distress"],
        ["Structural Zero Capital", "pl.col('RBCRWAJ') == 0.0 before 1990Q1", "100.0% zero rate prior to 1990", "Engineered is_pre_basel flag + _isna", "Basel I took legal effect in 1990; not solvency failure"],
        ["Nonpositive Assets / Equity", "pl.col('ASSET') <= 0 | pl.col('EQ') <= 0", "ASSET <= 0: 0 rows; EQ < 0: 1,842 rows", "cap_ratio clipped; neg_equity_flag = 1", "Technical insolvency is a crucial distress predictor"],
        ["Unresolved Entity Exits", "inst_end_date present but no failure match", "63,380 bank-quarters across panel", "Right-censored (excluded from test labels)", "Prevents treating voluntary mergers as bank failures"],
        ["Temporal Reporting Gaps", "q_idx - lag(q_idx) > 1 for same CERT", "2,418 sporadic gap transitions", "Lags compute null via calendar index", "Prevents false quarterly momentum calculations"]
    ]
    add_styled_table(
        doc,
        headers=headers_t21,
        data_rows=data_t21,
        col_widths=[1.3, 1.4, 1.2, 1.2, 1.4],
        caption="Table 2.1: Automated Evidence-Based Data-Quality Audit Framework, Defect Detection Rules, and Remediation Treatments",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_heading_2(doc, "2.2 Bank Lifecycle and Event Classification Taxonomy")
    add_paragraph(
        doc,
        "A foundational defect in naive bank risk modeling is the failure to distinguish between fundamentally different bank termination events. In empirical banking data, institutions disappear from the Call Report panel for several mutually exclusive reasons: (1) regulatory failure and receivership closure by the FDIC; (2) unassisted commercial merger or acquisition by another operating institution; (3) voluntary liquidation and charter surrender; and (4) structural reorganization or conversion to a non-reporting entity. Conflating unassisted commercial mergers with supervisory failures introduces catastrophic false-positive bias into predictive models, as healthy institutions absorbed by larger peers would be misclassified as insolvent distress events. Conversely, treating all unknown disappearances as healthy banks induces false-negative label noise.",
        bold_prefix="Event Taxonomy Dilemma: "
    )
    add_paragraph(
        doc,
        "The pipeline reconciles event dates using three primary historical timestamps: failure_date (the official date the FDIC was appointed receiver), inst_end_date (the corporate dissolution date recorded in FDIC structure tables), and confirmed_exit_date. A granular diagnostic audit revealed a specific subset of 29 unique CERTs where inst_end_date precedes failure_date in historical registry tables. An exhaustive impact review (docs/evidence/lifecycle_exception_review.md) established that this 29-CERT conflict subset accounts for exactly 106 positive bank-quarter observations in the historical Development panel (prior to 2008), and exactly ZERO positive bank-quarter observations in the held-out Test panel (2009Q1–2025Q2). In accordance with conservative research governance, all unknown non-failure disappearances remain strictly censored rather than re-labeled as healthy negatives, ensuring zero artificial contamination of held-out Test evaluation.",
        bold_prefix="Lifecycle Conflict Adjudication: "
    )

    add_heading_2(doc, "2.3 Point-in-Time Panel Construction and Temporal Splitting")
    add_paragraph(
        doc,
        "The master failure registry (failures.parquet) contains 4,117 raw historical failure records dating back to the inception of the FDIC in 1934. Table 2.2 documents the systematic reconciliation between raw failure records and the active financial panel. After excluding 488 records with null CERT numbers and deduplicating 44 multi-agreement filings for single failure events, exactly 3,585 unique failed bank charters remain. Of these, 3,241 unique failed CERTs matched commercial banks filing active Call Reports within our 1984Q1–2026Q2 study window. The remaining 344 failure registry entries represent historical closures that do not appear in the 1984Q1–2026Q2 Call Report panel; qualified possibilities include failures occurring prior to the 1984 Call Report inception, non-depository trust entities or specialized institutions exempt from standard commercial bank Call Report filing, or unlinked historical charter identifiers. Furthermore, the dataset constitutes a report-date Point-in-Time (PIT) panel indexed by Call Report date (REPDTE), which establishes accounting quarter boundaries and prevents forward lookahead. However, because banks submit filings within a statutory 30-to-45-day reporting grace period and may subsequently file accounting restatements, report-date PIT reflects as-reported accounting dates rather than a physical real-time database snapshot archive (vintage PIT).",
        bold_prefix="Failure Registry Reconciliation: "
    )

    # Table 2.2 Failure Reconciliation
    headers_t22 = ["Audit Category", "Raw Rows", "Excluded / Dedup", "Unique Entities", "Matched in Panel", "Accounting Reason / Notes"]
    data_t22 = [
        ["FDIC Historical Failures", "4,117", "488 Null CERT", "3,585 CERTs", "3,241 CERTs", "Historical closures dating back to 1934"],
        ["Duplicate Event Filings", "44", "44 Multi-action", "0 Deduplicated", "N/A", "Multiple resolution agreements for single failure"],
        ["Matched in Active Panel", "3,241", "0", "3,241 CERTs", "3,241 CERTs", "Commercial banks active in 1984Q1–2026Q2"],
        ["Unmatched Historical", "344", "0", "344 CERTs", "0 Matched", "Closures prior to 1984, non-depository trust entities, or unlinked charter IDs"]
    ]
    add_styled_table(
        doc,
        headers=headers_t22,
        data_rows=data_t22,
        col_widths=[1.5, 0.9, 1.1, 1.0, 1.0, 1.0],
        caption="Table 2.2: Master FDIC Failure Reconciliation Audit (Registry vs. Active Financial Panel)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_paragraph(
        doc,
        "The early-warning target variable y_{i, t+4} is formally defined as a binary indicator: y_{i, t+4} = 1 if institution i is closed by regulatory authorities within the forward four-quarter horizon [t+1, t+4], and 0 otherwise. To prevent information leakage, the temporal partitioning architecture implements four non-overlapping horizons: (1) Development Panel (1984Q1–2007Q4: 1,176,223 valid labeled bank-quarters, 10,153 failure events, 2,680 unique failed banks); (2) 1-Year Embargo Quarantine (calendar year 2008: 33,039 valid labeled bank-quarters, 402 failure events, 176 unique failed banks) designed to completely quarantine forward-looking distress signals from contaminating Test evaluation; (3) Out-of-Time Test Panel (2009Q1–2025Q2: 386,964 valid labeled bank-quarters, 1,775 failure events, 500 unique failed banks); and (4) Terminal Right-Censored Horizon (2025Q3–2026Q2: 17,501 observations) where the 4-quarter forward outcome window has not yet matured.",
        bold_prefix="Temporal Partition Architecture: "
    )

    # Table 2.3 Temporal Split
    headers_t23 = ["Split Segment", "Calendar Horizon", "Panel Rows", "Censored Exits", "Valid Labeled Obs", "Positives (y=1)", "Prevalence (%)", "Unique Failed CERTs"]
    data_t23 = [
        ["Development", "1984Q1–2007Q4", "1,224,942", "48,719", "1,176,223", "10,153", "0.863%", "2,680 Unique Charters"],
        ["Embargo Gap", "2008Q1–2008Q4", "33,966", "927", "33,039", "402", "1.217%", "176 Unique Charters"],
        ["Out-of-Time Test", "2009Q1–2025Q2", "400,698", "13,734", "386,964", "1,775", "0.459%", "500 Unique Charters"],
        ["Terminal Horizon", "2025Q3–2026Q2", "17,501", "17,501", "0", "0", "N/A", "N/A (Right-Censored)"]
    ]
    add_styled_table(
        doc,
        headers=headers_t23,
        data_rows=data_t23,
        col_widths=[1.1, 1.0, 0.8, 0.8, 0.9, 0.8, 0.6, 0.5],
        caption="Table 2.3: Temporal Partition Architecture, Censoring Controls, and Labeled Population Breakdown",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_heading_2(doc, "2.4 Regulatory Capital Structural Zero Reporting Audit")
    add_paragraph(
        doc,
        "Figure 2 and Table 2.4 document a critical regulatory accounting break discovered during the panel audit. Prior to 1990Q1, regulatory reporting did not include Risk-Weighted Assets (RBCRWAJ), resulting in a 100.0% structural zero reporting rate across all insured institutions. Following the formal adoption of the Basel I Accord in 1990, risk-weighted reporting became legally mandatory, causing zero reporting rates to collapse abruptly to 0.3%. Tier 1 Risk-Based Capital (RBC1AAJ) exhibited 17.6% structural zeros in 1984, rapidly stabilizing below 0.4% post-1990. In recent periods (post-2020), non-reporting rose again to 36.4%–41.5% due to the enactment of the Community Bank Leverage Ratio (CBLR), which allowed qualifying institutions under $10 billion in assets to bypass risk-weighted calculations. Naive machine learning models that treat structural zeroes as insolvent capital ratios would generate massive false-positive alarms. The pipeline resolves this by engineering an explicit binary indicator (is_pre_basel = 1 for REPDTE < 19900331) and tracking missingness flags (_isna) across all capital metrics.",
        bold_prefix="Accounting Structural Shift: "
    )

    add_figure(
        doc,
        figures_dir / "fig2_capital_regime_audit.png",
        "Figure 2: Longitudinal Regulatory Capital Variable Reporting and Structural Zero Audit (1984–2026). Data labels: RBCRWAJ is 100.0% zero in 1984–1989, dropping abruptly to 0.3% in 1990 upon Basel I implementation, then rising to 36.4%–41.5% post-2020 under the Community Bank Leverage Ratio (CBLR)."
    )

    add_figure(
        doc,
        figures_dir / "fig3_temporal_split_overview.png",
        "Figure 3: Temporal Split Architecture, Embargo Gap, and Regime Failure Prevalence. Panel 1: Valid observations across Development (1,176,223), Embargo (33,039), and Test (386,964). Panel 2: Baseline failure prevalence (0.863% Dev, 1.217% Embargo, 0.459% Test; 1,775 positive bank-quarters representing 500 unique failed bank charters)."
    )

    # ---------------------------------------------------------------------------
    # PART 3 – SCALABLE PROCESSING [25 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 3 – SCALABLE PROCESSING ENGINE BENCHMARK [25 POINTS]")

    add_heading_2(doc, "3.1 Polars Lazy API Implementation and Optimization Plan")
    add_paragraph(
        doc,
        "The core data engineering transformations were implemented using the Polars Lazy API (src/fdic_pipeline/workload.py). The measured benchmarking workload in workload.py represents an intensive seven-feature, calendar-aware financial risk workload (capital_ratio, loan_asset_ratio, liquidity_ratio, asset_growth_qoq, asset_growth_yoy, roa_std_4q, and cap_zscore_pit), rather than an execution of all 30 CAMELS features. This representative workload isolates the core computational bottlenecks: multi-quarter lags, calendar gap verification, rolling standard deviations over bank partitions, and cross-sectional quarterly z-score aggregations. Polars is an open-source DataFrame library written in Rust, built on top of the Apache Arrow columnar memory format. Rather than executing transformations eagerly step-by-step, Polars constructs an internal directed acyclic graph (DAG) representing the complete sequence of logical operations. When collect() is invoked, Polars' query optimizer compiles the logical plan into a highly optimized physical plan.",
        bold_prefix="Rust Vectorized Engine: "
    )
    add_paragraph(
        doc,
        "Analysis of the compiled Polars execution plan (artifacts/stageC/benchmark_1x_r3/polars_1x_plan.txt) demonstrates three critical optimizations implemented in code: (1) Projection Pushdown: The Parquet scanner evaluates PROJECT */9 COLUMNS, loading only the 9 required financial attributes directly from disk and ignoring unreferenced columns; (2) Predicate Pushdown: Row filtering operations are pushed directly into the storage scanner, skipping row groups based on Parquet statistics; and (3) Multithreaded Vectorized Windowing: Polars computes quarterly integer indices (_qid = year * 4 + quarter - 1), sorts by [CERT, REPDTE], and executes rolling window calculations (shift(1), shift(4), rolling_std(window_size=4)) partitioned over CERT using Rayon's work-stealing multithreaded scheduler across all 16 CPU cores without any Python Global Interpreter Lock (GIL) contention.",
        bold_prefix="Query Plan Optimization: "
    )

    add_heading_2(doc, "3.2 Eager pandas Baseline and Memory Overhead")
    add_paragraph(
        doc,
        "To establish a rigorous baseline, an identical analytical workload was implemented in pure pandas (Python 3.11 with pyarrow backend). Unlike Polars, pandas executes eagerly: every transformation immediately allocates intermediate memory buffers and executes synchronously on a single CPU thread due to Python's GIL. Grouping operations (df.groupby('CERT')) and rolling standard deviations force pandas to create Python object references and perform repeated memory copies. In our 1x baseline benchmark, pandas required 5.157 seconds to execute the feature pipeline and peaked at 794 MiB RSS memory, operating at only 325,210 rows per second.",
        bold_prefix="Eager Baseline Bottlenecks: "
    )

    add_heading_2(doc, "3.3 Distributed PySpark Local[*] and Catalyst Plan Execution")
    add_paragraph(
        doc,
        "To evaluate distributed execution, the identical feature engineering pipeline was implemented in Apache Spark (PySpark 3.5.3) running in Local[*] mode, configured with 8 shuffle partitions (spark.sql.shuffle.partitions = 8) and 4 GB JVM driver memory, utilizing all 16 available hardware threads. Analysis of Spark's Catalyst physical plan (artifacts/stageC/benchmark_1x_r3/spark_1x_plan.txt) reveals the structural mechanics of distributed execution on a single workstation:",
        bold_prefix="PySpark Architecture: "
    )
    add_paragraph(
        doc,
        "Catalyst decomposes the workload into multiple nested WindowExec operators: Window [lag(ASSET) ... RowFrame, -4, -4], Window [lag(_qid) ... RowFrame, -1, -1], Window [stddev_samp(ROA) ... RowFrame, -3, currentrow], and Window [avg(capital_ratio) ... RowFrame, unboundedpreceding, unboundedfollowing]. While Catalyst successfully optimizes expressions, running Spark on a single workstation incurs severe architectural penalties: (1) JVM startup and Catalyst query compilation impose a mandatory ~10–14 second base latency tax; (2) data marshaling across the Py4J socket interface between Python and the Java Virtual Machine creates substantial serialization overhead; and (3) partition-level sorting and window coordination consume significant CPU cycles. Consequently, PySpark Local[*] required 14.757 seconds to process the 1x panel—running 18.52x slower than Polars.",
        bold_prefix="Catalyst Plan Analysis: "
    )

    add_heading_2(doc, "3.4 Cross-Engine Numeric Equivalence Verification")
    add_paragraph(
        doc,
        "A critical engineering requirement when comparing data processing engines is verifying that all implementations produce mathematically equivalent financial features. Discrepancies often emerge from differing floating-point accumulation orders, integer division rules, or rolling window boundary handling. The pipeline executes an automated numerical parity audit (artifacts/stageC/*/numeric_equivalence.json) that performs an outer join across Polars and PySpark outputs on primary keys (CERT, REPDTE) and measures absolute differences across all engineered attributes.",
        bold_prefix="Equivalence Audit Protocol: "
    )

    # Table 3.1 Numeric Equivalence
    headers_t31 = ["Engineered CAMELS Feature", "Polars Data Type", "PySpark Data Type", "Max Absolute Difference", "Mathematical Verification Status"]
    data_t31 = [
        ["capital_ratio", "Float64 Array", "DoubleType Column", "0.000000e+00", "PASS (Exact Bitwise Parity)"],
        ["loan_asset_ratio", "Float64 Array", "DoubleType Column", "0.000000e+00", "PASS (Exact Bitwise Parity)"],
        ["liquidity_ratio", "Float64 Array", "DoubleType Column", "0.000000e+00", "PASS (Exact Bitwise Parity)"],
        ["asset_growth_qoq", "Float64 Array", "DoubleType Column", "0.000000e+00", "PASS (Exact Bitwise Parity)"],
        ["asset_growth_yoy", "Float64 Array", "DoubleType Column", "0.000000e+00", "PASS (Exact Bitwise Parity)"],
        ["roa_std_4q", "Float64 Array", "DoubleType Column", "5.684342e-14", "PASS (< 1.0e-06 Machine Epsilon)"],
        ["cap_zscore_pit", "Float64 Array", "DoubleType Column", "1.421085e-13", "PASS (< 1.0e-06 Machine Epsilon)"]
    ]
    add_styled_table(
        doc,
        headers=headers_t31,
        data_rows=data_t31,
        col_widths=[1.5, 1.1, 1.2, 1.3, 1.4],
        caption="Table 3.1: Cross-Engine Numeric Equivalence Audit (Polars Lazy API vs. PySpark Catalyst Feature Outputs)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_heading_2(doc, "3.5 Multi-Scale Empirical Performance Benchmark (27 Measured Runs)")
    add_paragraph(
        doc,
        "The empirical benchmark evaluated pandas, Polars Lazy API, and PySpark Local[*] across 27 executed experimental runs recorded in artifacts/stageC/final/benchmark_runs.csv. The benchmark tested three scales: 1x Baseline (1,677,107 clean bank-quarters), 2x Synthetic (3,354,214 rows), and 5x Synthetic (8,385,535 rows). Each engine was measured three times at each scale; Table 3.2 and Table 3.3 report the verified 3-run medians and memory RSS footprints.",
        bold_prefix="Benchmark Methodology: "
    )

    # Table 3.2 1x Baseline Summary
    headers_t32 = ["Processing Engine", "Execution Framework", "Median Wall Time", "Compute Latency", "Memory RSS", "Speedup vs. pandas", "Processing Throughput"]
    data_t32 = [
        ["pandas (Baseline)", "Eager In-Memory (Single Thread)", "5.157 s (5.16 s)", "4.94 s", "794 MiB", "1.00x (Baseline)", "325,210 rows/s"],
        ["Polars Lazy API", "Rust Vectorized (16 Threads)", "0.797 s (0.80 s)", "0.26 s", "774 MiB", "6.47x Faster", "2,104,275 rows/s"],
        ["PySpark (Local[*])", "JVM Catalyst (16 Cores)", "14.757 s (14.76 s)", "10.57 s", "1,013 MiB", "0.35x (Slower)", "113,648 rows/s"]
    ]
    add_styled_table(
        doc,
        headers=headers_t32,
        data_rows=data_t32,
        col_widths=[1.4, 1.3, 0.9, 0.7, 0.7, 0.8, 0.7],
        caption="Table 3.2: 1x Empirical Baseline Engine Benchmark Summary (1,677,107 Bank-Quarter Observations)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        figures_dir / "fig4_engine_benchmark_1x.png",
        "Figure 4: Single-Node Engine Benchmark at 1x Baseline Scale (1.68M Bank-Quarter Observations). Panel 1: Latency (Polars 0.80s vs. pandas 5.16s vs. PySpark 14.76s). Panel 2: Peak process-tree RSS (Polars 774 MiB, pandas 794 MiB, PySpark 1,013 MiB)."
    )

    # Table 3.3 Multi-Scale Benchmark
    headers_t33 = ["Scale Factor", "Synthetic Bank-Quarters", "pandas Median Wall (s)", "Polars Median Wall (s)", "PySpark Median Wall (s)", "Polars Speedup vs. pandas", "Polars Speedup vs. PySpark"]
    data_t33 = [
        ["1x Baseline", "1,677,107 rows", "5.157 s", "0.797 s", "14.757 s", "6.47x Faster", "18.52x Faster"],
        ["2x Synthetic", "3,354,214 rows", "9.133 s", "1.559 s", "17.988 s", "5.86x Faster", "11.54x Faster"],
        ["5x Synthetic", "8,385,535 rows", "21.940 s", "2.464 s", "31.514 s", "8.90x Faster", "12.79x Faster"]
    ]
    add_styled_table(
        doc,
        headers=headers_t33,
        data_rows=data_t33,
        col_widths=[1.0, 1.3, 0.9, 0.9, 0.9, 0.8, 0.7],
        caption="Table 3.3: Empirical Multi-Scale Processing Benchmark Across 27 Executed Experimental Runs (1x to 5x)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        figures_dir / "fig5_synthetic_scaling_5x.png",
        "Figure 5: Empirical Multi-Scale Engine Benchmark Across 1x, 2x, and 5x Synthetic Replications. Panel 1: Latency scaling (Polars 0.80s -> 1.56s -> 2.46s; pandas 5.16s -> 9.13s -> 21.94s; Spark 14.76s -> 17.99s -> 31.51s). Panel 2: Memory RSS scaling (pandas 3,555 MiB at 5x; Polars 2,347 MiB; Spark 1,443 MiB). 10x was not measured."
    )

    add_heading_2(doc, "3.6 Distributed Cluster Break-Even and Hardware Justification Boundary")
    add_paragraph(
        doc,
        "It is essential to clarify that 2x and 5x scales represent synthetic replications of the analytical bank-quarter workload, not additional genuine FDIC reporting institutions. As documented in docs/evidence/part5_integrity_status.json, 10x scale was NOT measured on this host workstation due to physical RAM limitations. Furthermore, across all measured scales (1x to 5x), Polars Lazy API decisively outperforms PySpark Local[*], maintaining an 11.5x to 18.5x speedup. There is ZERO empirical evidence of Spark overtaking Polars at 2x or 5x in local workstation execution.",
        bold_prefix="Synthetic Workload Disclosure: "
    )
    add_paragraph(
        doc,
        "Under what conditions is a distributed Spark cluster justified? Based on our empirical measurements, deploying a multi-node distributed Spark cluster is justified if and only if: (1) Working set size exceeds available physical host memory, causing operating system page thrashing and out-of-memory (OOM) kernel crashes; (2) Data resides across distributed cloud object stores (Amazon S3, HDFS, Azure Data Lake) requiring partition-level distributed shuffle across independent physical network nodes; (3) Analytical pipelines require real-time integration with distributed streaming brokers (Apache Kafka); or (4) Modeling pipelines utilize distributed cluster MLlib algorithms. For historical FDIC Call Report analytics on single-node workstations where the dataset fits in physical memory, Polars Lazy API is the definitively superior engine in latency, memory efficiency, and operational simplicity.",
        bold_prefix="Cluster Break-Even Boundary: "
    )

    # ---------------------------------------------------------------------------
    # PART 4 – FEATURE PIPELINE [15 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 4 – POINT-IN-TIME FEATURE ENGINEERING PIPELINE [15 POINTS]")

    add_heading_2(doc, "4.1 CAMELS Feature Selection and Financial Interpretability")
    add_paragraph(
        doc,
        "The feature engineering pipeline operationalizes the supervisory CAMELS rating taxonomy, which regulatory examiners use to evaluate bank safety and soundness. Specifically, the feature space is composed of CAMELS-inspired financial indicators augmented by size, growth and peer-relative information. In regulatory CAMELS supervision, 'S' formally designates Sensitivity to Market Risk; our feature pipeline operationalizes core CAMELS dimensions and explicitly augments them with institutional scale (log_asset), balance sheet growth momentum (asset_growth_qoq, asset_growth_yoy), and peer-relative decile positioning (cap_zscore_q, roa_zscore_q, npl_zscore_q). The feature contract (docs/evidence/feature_contract.md) defines exactly 30 Development-available base financial features, plus 30 explicit missingness indicators (_isna), producing a verified predictor space of 60 columns. Table 4.1 details the economic rationale, mathematical formulations, and predictive importance across all active dimensions.",
        bold_prefix="CAMELS Taxonomy Architecture: "
    )

    # Table 4.1 Master Feature Table
    headers_t41 = ["CAMELS Dimension", "Feature Name", "FDIC Financial Formula", "LightGBM Gain", "LR Coef", "Economic Intuition & Supervisory Role"]
    data_t41 = [
        ["C - Capital", "cap_ratio", "EQ / ASSET", "654,601", "-2.474", "Primary equity leverage buffer; top failure predictor"],
        ["E - Earnings", "roa", "ROA (reported field)", "182,416", "-0.166", "Core operational profitability; absorbs credit losses"],
        ["C - Capital", "rbc_tier1", "RBC1AAJ (reported field)", "63,167", "-0.302", "Basel Tier 1 risk-based capital adequacy"],
        ["C - Capital", "cap_zscore_q", "(cap - mean_q) / std_q", "52,559", "+0.282", "Peer-relative capitalization decile within quarter"],
        ["A - Asset Quality", "npl_ratio", "NCLNLS / LNLSNET", "45,567", "+0.007", "Non-performing loan burden and credit impairment"],
        ["E - Earnings", "roe", "ROE (reported field)", "45,101", "-0.204", "Return on book equity; shareholder capital efficiency"],
        ["C - Capital", "rbc_total", "RBCRWAJ (reported field)", "33,888", "-2.439", "Total Basel risk-weighted regulatory capital"],
        ["L - Liquidity", "liq_dep_ratio", "(CHBAL + SC) / DEP", "23,455", "+0.363", "Liquid cash & securities coverage of deposit base"],
        ["E - Earnings", "roa_std_4q", "rolling_std(roa, 4Q)", "22,433", "+0.073", "Earnings stream volatility; instability precedes insolvency"],
        ["Augmented: Growth", "asset_growth_yoy", "ASSET_t / ASSET_{t-4} - 1", "21,353", "-0.078", "Aggressive balance sheet expansion flag"]
    ]
    add_styled_table(
        doc,
        headers=headers_t41,
        data_rows=data_t41,
        col_widths=[1.1, 1.2, 1.4, 0.9, 0.8, 1.1],
        caption="Table 4.1: Top 10 Active CAMELS Features Ranked by LightGBM Split Gain and Logistic Regression Coefficients",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_figure(
        doc,
        figures_dir / "fig7_top10_camels_importance.png",
        "Figure 7: Top 10 CAMELS Feature Importance Ranked by LightGBM Split Gain. Data labels: cap_ratio (654,601), roa (182,416), rbc_tier1 (63,167), cap_zscore_q (52,559), npl_ratio (45,567), roe (45,101), rbc_total (33,888), liq_dep_ratio (23,455), roa_std_4q (22,433), asset_growth_yoy (21,353)."
    )

    add_paragraph(
        doc,
        "Crucially, the feature store excludes eff_ratio (efficiency ratio derived from EEFFR) and core_dep_ratio because these line items are structurally absent in historical Call Reports prior to 2001. Previously published draft versions referenced an obsolete 31-feature / 62-predictor specification where eff_ratio_isna was a degenerate constant column equal to 1.0. The pipeline was rigorously corrected to strictly enforce the 30 base features / 60 predictors contract.",
        bold_prefix="Feature Store Normalization: "
    )

    add_heading_2(doc, "4.2 Anti-Leakage Feature Construction and Calendar Indexing")
    add_paragraph(
        doc,
        "A notorious source of data leakage in longitudinal financial panels occurs when lag variables are computed via sequential row shifts (e.g., .shift(1)). If an institution fails to file for two quarters, a naive row shift inadvertently compares quarter t against quarter t-3, creating false momentum indicators. To ensure absolute temporal integrity, the pipeline engineers an integer calendar quarter index: q_idx = year * 4 + ((month - 1) // 3). Lags and growth rates are computed strictly conditional on exact calendar spacing: asset_growth_qoq is populated if and only if q_idx - lag(q_idx) == 1; asset_growth_yoy is populated if and only if q_idx - lag(q_idx) == 4; and rolling standard deviations enforce q_idx - lag(q_idx, 3) == 3 with exactly 4 valid non-null quarterly observations. When reporting gaps occur, the feature evaluates to null rather than calculating an invalid growth rate.",
        bold_prefix="Calendar Indexing Mathematics: "
    )

    add_heading_2(doc, "4.3 Train-Only Preprocessing Pipeline and Invariance Testing")
    add_paragraph(
        doc,
        "To prevent look-ahead contamination during preprocessing, all feature transformations are encapsulated in a strict LeakageSafePreprocessor (src/fdic_pipeline/features.py). Continuous predictors undergo two-sided Winsorization at the 1st and 99th percentiles to mitigate extreme Call Report outliers, followed by training-set median imputation for missing values, and parametric mean/standard-deviation Z-score standardization: x_norm = (clip(x, p01, p99) - mean_tr) / std_tr. Imputation medians, Winsorization bounds, and standardization moments are fitted EXCLUSIVELY on the labeled training partition. The learned transformation parameters are frozen and serialized to artifacts/features/preprocessor_dev_params.json, and subsequently applied to transform the held-out Test split (2009Q1–2025Q2) without re-fitting.",
        bold_prefix="Train-Only Preprocessing: "
    )
    add_paragraph(
        doc,
        "The pipeline's anti-leakage architecture was validated via automated synthetic future-perturbation and invariance unit tests (tests/test_feature_leakage.py, tests/test_fold_local_feature_selection.py, and tests/test_cv_feature_local_guard.py; 15 passed). These tests inject synthetic extreme values and future failure labels into the Test or Validation partitions and verify that Development feature values, imputation statistics, and fold-local feature lists remain 100% invariant. Following an independent CV audit (docs/evidence/cv_feature_availability_audit.md), src/fdic_pipeline/model.py was patched with select_fold_available_features() so that CV feature availability is selected strictly independently from each fold's Training partition rather than across the full Development set (1984–2007). As verified in docs/evidence/cv_fold_local_impact_20261125_145302_363270.md, Fold 1 (Train: 1984Q1–1997Q4) drops nonperf_asset_ratio (29 active features, because Call Report item P3ASSET was first introduced in 2001Q1), whereas Fold 2, Fold 3, and the final full-Development model (239,942 valid observations) retain all 30 features. The final model was not retrained and published held-out Test metrics remain untouched.",
        bold_prefix="Invariance Testing & Disclosure: "
    )

    # ---------------------------------------------------------------------------
    # PART 5 – MODELLING & VALIDATION [15 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 5 – PREDICTIVE MODELING & EMPIRICAL VALIDATION [15 POINTS]")

    add_heading_2(doc, "5.1 Model Selection Rationales and Baseline Algorithms")
    add_paragraph(
        doc,
        "Three complementary model architectures were evaluated to establish a comprehensive early-warning benchmark: (1) L2-Regularized Logistic Regression (Ridge): Serves as the primary interpretable linear baseline widely utilized in banking supervision; (2) LightGBM Classifier: A state-of-the-art gradient boosting decision tree (GBDT) algorithm capable of capturing complex non-linear risk interactions, threshold effects, and structural collinearity without requiring feature selection; and (3) PySpark MLlib Logistic Regression: Demonstrates horizontal distributed model training and scoring across enterprise Spark clusters.",
        bold_prefix="Algorithm Architecture: "
    )

    add_heading_2(doc, "5.2 Expanding Window Cross-Validation Architecture")
    add_paragraph(
        doc,
        "Random k-fold cross-validation is fatally invalid for longitudinal financial panels because randomly partitioning bank-quarters leaks future macro-financial crisis information into training folds. To enforce strict temporal validity, predefined baseline model configurations were evaluated exclusively on the Development panel (1984Q1–2007Q4) using a 3-fold expanding time-series cross-validation scheme with an absolute 4-quarter purging buffer separating training and validation windows. Within each fold, active feature availability is selected strictly independently from that fold's own Training partition (select_fold_available_features(tr, BASE_FEATURES) in src/fdic_pipeline/model.py) prior to fitting LeakageSafePreprocessor: Fold 1 (Train: 1984Q1–1997Q4, 809,297 rows) selects 29 features (excluding nonperf_asset_ratio), while Fold 2 (1984Q1–2001Q4, 965,816 rows) and Fold 3 (1984Q1–2004Q4, 1,074,176 rows) retain all 30 features.",
        bold_prefix="Expanding Window Protocol: "
    )

    # Table 5.1 CV Performance
    headers_t51 = ["Validation Fold", "Model Architecture", "Validation Window", "Train Feats", "Val Obs", "Val Pos", "PR-AUC", "ROC-AUC", "Recall @ Top 5%", "Brier Score"]
    data_t51 = [
        ["Fold 1", "Logistic Regression", "1999Q1–2002Q4", "29", "152,958", "104", "0.2106", "0.8415", "63.46%", "0.00061"],
        ["Fold 1", "LightGBM Classifier", "1999Q1–2002Q4", "29", "152,958", "104", "0.2392", "0.8930", "74.04%", "0.00058"],
        ["Fold 2", "Logistic Regression", "2003Q1–2005Q4", "30", "105,955", "20", "0.0651", "0.7805", "70.00%", "0.00025"],
        ["Fold 2", "LightGBM Classifier", "2003Q1–2005Q4", "30", "105,955", "20", "0.0763", "0.8987", "75.00%", "0.00021"],
        ["Fold 3", "Logistic Regression", "2006Q1–2007Q4", "30", "67,468", "55", "0.0840", "0.8045", "43.64%", "0.00079"],
        ["Fold 3", "LightGBM Classifier", "2006Q1–2007Q4", "30", "67,468", "55", "0.1183", "0.9023", "54.55%", "0.00078"]
    ]
    add_styled_table(
        doc,
        headers=headers_t51,
        data_rows=data_t51,
        col_widths=[0.65, 1.25, 1.05, 0.45, 0.65, 0.45, 0.5, 0.5, 0.6, 0.4],
        caption="Table 5.1: 3-Fold Expanding Time-Series Cross-Validation Performance with Fold-Local Feature Selection (Development Panel, 1984–2007)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )
    add_paragraph(
        doc,
        "In the controlled fold-local CV audit (docs/evidence/cv_fold_local_impact_20261125_145302_363270.md), dropping the all-null nonperf_asset_ratio in Fold 1 improves Logistic Regression AP from 0.154802 to 0.210628 (+0.055826), ROC-AUC from 0.839364 to 0.841550 (+0.002186), and Brier Score from 0.00209 to 0.00061. LightGBM Fold 1 (AP 0.239183, ROC-AUC 0.892996) and all Fold 2/Fold 3 metrics exhibit 0.000000 change between pre-patch and post-patch current-source CV (Mean |Δp| = 0). Pre-patch current-source LR figures (0.1548 / 0.0651 / 0.0840) differ slightly from the earlier archived dev_timeseries_cv.csv (0.1540 / 0.0680 / 0.0869), whereas LightGBM is identical.",
        bold_prefix="Fold-Local CV Audit Impact: "
    )

    add_heading_2(doc, "5.3 Highly Imbalanced Metric Evaluation and Out-of-Time Test Results")
    add_paragraph(
        doc,
        "Because bank failures represent less than 0.5% of quarterly observations (0.459% in the held-out Test panel), standard Accuracy and ROC-AUC metrics can be dangerously misleading. A trivial null classifier that predicts zero failures achieves 99.54% accuracy despite offering zero supervisory utility. Consequently, model performance was evaluated using Precision-Recall Area Under the Curve (PR-AUC / Average Precision), Brier probability calibration scores, and Top-Decile Alert Recall.",
        bold_prefix="Imbalanced Evaluation Metrics: "
    )

    # Table 5.2 Out-of-Time Test Performance
    headers_t52 = ["Model Architecture", "Test Observations", "Test Positives", "Average Precision (AP)", "ROC-AUC", "Recall @ Top 5%", "Recall @ Top 10%", "Brier Score"]
    data_t52 = [
        ["Logistic Regression", "386,964", "1,775", "0.6795 (0.679477)", "0.9863 (0.986308)", "93.58%", "96.39%", "0.00231"],
        ["LightGBM Classifier", "386,964", "1,775", "0.6682 (0.668168)", "0.9861 (0.986115)", "93.41%", "96.45%", "0.00242"],
        ["PySpark MLlib LogReg", "386,964", "1,775", "0.5699 (0.5547 native)", "0.9794 (0.979361)", "91.20%", "94.80%", "0.00295"]
    ]
    add_styled_table(
        doc,
        headers=headers_t52,
        data_rows=data_t52,
        col_widths=[1.5, 0.9, 0.8, 1.1, 0.8, 0.8, 0.8, 0.5],
        caption="Table 5.2: Out-of-Time Test Performance on Held-Out Evaluation Panel (2009Q1–2025Q2, 386,964 Bank-Quarters)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        figures_dir / "fig6_test_pr_and_calibration.png",
        "Figure 6: Out-of-Time Test Precision-Recall and Probability Calibration Curves (2009Q1–2025Q2). Panel 1: Precision-Recall curves against 0.459% test baseline prevalence. Panel 2: Calibration reliability across deciles (Logistic Regression Brier = 0.00231, LightGBM Brier = 0.00242)."
    )

    add_paragraph(
        doc,
        "An essential metric distinction must be highlighted regarding PySpark MLlib: Spark's native BinaryClassificationEvaluator computes areaUnderPR via trapezoidal approximation (0.554674), whereas scikit-learn computes Average Precision via rectangular step integration (0.569949). Both reflect the exact same underlying predicted probabilities; the numerical divergence is purely an artifact of integration conventions. Logistic Regression achieves a marginally higher point AP (0.6795 vs. 0.6682) because linear log-odds assign extremely sharp probabilities to obvious capital-depleted institutions, whereas LightGBM spreads probability density over borderline cases, yielding superior recall under supervisory cost constraints.",
        bold_prefix="Metric Parity & Interpretation: "
    )

    add_heading_2(doc, "5.4 Asymmetric Supervisory Loss and Cost-Sensitive Alarm Thresholding")
    add_paragraph(
        doc,
        "In bank supervision, false positives and false negatives carry vastly asymmetric economic costs. A False Positive (auditing a healthy bank) costs the supervisory agency approximately CFP = 0.005 * total assets in operational staff hours. A False Negative (missing an insolvent bank), however, forces the FDIC to liquidate assets in fire sales, deplete the Deposit Insurance Fund, and absorb catastrophic resolution losses. An empirical analysis of 1,275 historical FDIC resolutions in artifacts/model_30feature_corrected/empirical_cost_estimation.csv establishes that the median resolution loss rate is L_FN = 20.17% of total assets. Assuming an on-site supervisory examination cost CFP = 0.50% of assets (explicitly noted as a scenario benchmark), the implied empirical supervisory loss ratio is: r = L_FN / CFP = 0.2017 / 0.0050 = 40.3:1.",
        bold_prefix="Loss Ratio Derivation: "
    )
    add_paragraph(
        doc,
        "The optimal operational alert threshold tau* was identified by minimizing the expected supervisory loss function on out-of-fold Development predictions: L(tau) = CFP * FP(tau) + L_FN * FN(tau). Specifically, tau* was evaluated over a 501-point empirical quantile grid spanning observed out-of-fold predicted probabilities (including boundary thresholds 0.0 and 1.0). Optimal thresholds were frozen strictly on Development data and saved to artifacts/model_30feature_corrected/frozen_development_decisions.json (tau* = 0.0201 for LightGBM; tau* = 0.2755 for Logistic Regression under the 40.3:1 loss matrix). In Table 5.3, Alert Rate (%) denotes the fraction of eligible held-out Test bank-quarter observations flagged (e.g., 5,230 FP + 1,656 TP = 6,886 alerts out of 386,964 test quarters = 1.78%), and cost reductions represent modeled expected reductions under the assumed loss function. Table 5.3 reports the held-out Test evaluation across three cost scenarios.",
        bold_prefix="Cost-Sensitive Thresholding: "
    )

    # Table 5.3 Cost-Sensitive Decisions
    headers_t53 = ["Cost Scenario", "Model Architecture", "Frozen Tau*", "True Pos (TP)", "False Pos (FP)", "False Neg (FN)", "Precision (%)", "Bank-Q Recall (%)", "Unique Banks Captured", "Alert Rate (%)", "Expected Cost Units"]
    data_t53 = [
        ["Conservative (10:1)", "Logistic Regression", "0.9996", "0", "0", "1,775", "0.00%", "0.00%", "0 / 500 (0.0%)", "0.00%", "17,750.0"],
        ["Conservative (10:1)", "LightGBM Classifier", "0.0201", "1,656", "5,230", "119", "24.05%", "93.30%", "484 / 500 (96.8%)", "1.78%", "6,420.0"],
        ["Loss-Informed (40.3:1)", "Logistic Regression", "0.2755", "1,175", "683", "600", "63.24%", "66.20%", "451 / 500 (90.2%)", "0.48%", "24,863.0"],
        ["Loss-Informed (40.3:1)", "LightGBM Classifier", "0.0201", "1,656", "5,230", "119", "24.05%", "93.30%", "484 / 500 (96.8%)", "1.78%", "10,025.7"],
        ["High Penalty (50:1)", "Logistic Regression", "0.2755", "1,175", "683", "600", "63.24%", "66.20%", "451 / 500 (90.2%)", "0.48%", "30,683.0"],
        ["High Penalty (50:1)", "LightGBM Classifier", "0.0201", "1,656", "5,230", "119", "24.05%", "93.30%", "484 / 500 (96.8%)", "1.78%", "11,180.0"]
    ]
    add_styled_table(
        doc,
        headers=headers_t53,
        data_rows=data_t53,
        col_widths=[1.1, 1.1, 0.5, 0.5, 0.5, 0.5, 0.6, 0.6, 0.8, 0.5, 0.8],
        caption="Table 5.3: Supervisory Cost Matrix Sensitivity Analysis (Optimal Thresholds Frozen from Development OOF)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    headers_t53b = ["Cost Scenario", "Model", "Hist. Frozen τ*", "Pre-Patch OOF τ", "Post-Audit OOF τ", "Δτ (Audit)", "Pre-Patch OOF Cost", "Post-Audit OOF Cost"]
    data_t53b = [
        ["Conservative (10:1)", "Logistic Regression", "0.9996", "0.99961394", "0.03219052", "-0.96742342", "1,780.0", "1,684.0"],
        ["Conservative (10:1)", "LightGBM Classifier", "0.0201", "0.02008020", "0.02008020", "+0.00000000", "1,618.0", "1,618.0"],
        ["Loss-Informed (40.3:1)", "Logistic Regression", "0.2755", "0.28266263", "0.03219052", "-0.25047211", "5,719.1", "5,017.0"],
        ["Loss-Informed (40.3:1)", "LightGBM Classifier", "0.0201", "0.02008020", "0.02008020", "+0.00000000", "4,769.2", "4,769.2"],
        ["High Penalty (50:1)", "Logistic Regression", "0.2755", "0.28266263", "0.03219052", "-0.25047211", "6,951.0", "6,084.0"],
        ["High Penalty (50:1)", "LightGBM Classifier", "0.0201", "0.02008020", "0.02008020", "+0.00000000", "5,778.0", "5,778.0"]
    ]
    add_styled_table(
        doc,
        headers=headers_t53b,
        data_rows=data_t53b,
        col_widths=[1.05, 1.05, 0.65, 0.8, 0.8, 0.75, 0.7, 0.7],
        caption="Table 5.3b: Post-Audit Development-Only OOF Threshold Comparison (Historical Frozen Policy vs. Pre-Patch vs. Fold-Local Corrected)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )
    add_paragraph(
        doc,
        "Table 5.3b distinguishes the originally frozen pre-Test policy (artifacts/model_30feature_corrected/frozen_development_decisions.json, used for Table 5.3) from the post-audit Development-only OOF sensitivity thresholds (docs/evidence/cv_fold_local_impact_20261125_145302_363270.md). LightGBM's optimal threshold (0.02008020) and OOF cost (4,769.2 at 40.3:1) are 100% invariant. For Logistic Regression, fold-local selection in Fold 1 shifts the post-audit OOF threshold at 40.3:1 from 0.28266263 (pre-patch reproduction) to 0.03219052. Because the held-out Test set has already been observed, this post-audit LR threshold is strictly a Development-only sensitivity finding; it was NOT evaluated as a pre-Test frozen policy, the final model was NOT retrained, and published Test metrics in Tables 5.2–5.4 remain unchanged.",
        bold_prefix="OOF Threshold Audit & Test Freeze Governance: "
    )

    add_heading_2(doc, "5.5 Macroeconomic Regime Sensitivity and Failure Non-Additivity")
    add_paragraph(
        doc,
        "Table 5.4 and Figure 8 evaluate out-of-time model robustness across three distinct regulatory and macroeconomic sub-regimes: (1) 2009Q1–2014Q4 (GFC & Crisis Aftermath: 172,562 bank-quarters, 1,646 failure events, 468 unique failed banks); (2) 2015Q1–2022Q4 (Low-Failure Economic Expansion: 169,519 bank-quarters, 107 failure events, 30 unique failed banks); and (3) 2023Q1–2025Q2 (Regional Banking Crisis: 44,883 bank-quarters, 22 failure events, 9 unique failed banks).",
        bold_prefix="Sub-Regime Breakdown: "
    )

    # Table 5.4 Sub-Regime Performance
    headers_t54 = ["Regulatory Sub-Regime", "Macroeconomic Context", "Test Bank-Qs", "Positives (y=1)", "Unique Failed Banks", "PR-AUC", "ROC-AUC", "Recall @ Top 5%", "Banks Captured (Base Tau)"]
    data_t54 = [
        ["2009Q1–2014Q4", "GFC & Crisis Aftermath", "172,562", "1,646", "468", "0.7045", "0.9910", "94.78%", "460 / 468 (98.3%)"],
        ["2015Q1–2022Q4", "Low-Failure Expansion", "169,519", "107", "30", "0.3427", "0.8987", "81.31%", "23 / 30 (76.7%)"],
        ["2023Q1–2025Q2", "Regional Bank Stress", "44,883", "22", "9", "0.1821", "0.8755", "50.00%", "5 / 9 (55.6%)"]
    ]
    add_styled_table(
        doc,
        headers=headers_t54,
        data_rows=data_t54,
        col_widths=[1.2, 1.3, 0.8, 0.7, 0.8, 0.5, 0.5, 0.7, 1.0],
        caption="Table 5.4: Model Discrimination and Capture Rates Across Three Out-of-Time Macroeconomic Sub-Regimes",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        figures_dir / "fig8_cost_and_regime_analysis.png",
        "Figure 8: Supervisory Expected Cost Analysis and Regime-Specific Recall Performance. Panel 1: Expected cost units across Conservative (10:1), Loss-Informed (40.3:1), and High Penalty (50:1) scenarios. Panel 2: Recall across regimes (94.8% GFC, 81.3% Expansion, 50.0% Regional Stress)."
    )

    add_paragraph(
        doc,
        "Accounting Non-Additivity Reconciliation: In Table 5.4, summing unique failed banks across the three sub-regimes yields 468 + 30 + 9 = 507, which exceeds the global test total of 500 unique failed banks. As verified in artifacts/model_30feature_corrected/regime_nonadditivity.json, this occurs because exactly 7 institutions span calendar boundary transitions (contributing positive failure labels in late 2014 and early 2015). Both counts are verified and reported transparently. Furthermore, regime breakdown reveals that while GFC credit failures were overwhelmingly detected (98.3%), capture rate dropped to 55.6% during the 2023 regional banking crisis, where institutions like Silicon Valley Bank collapsed due to intraday digital deposit runs uncaptured by quarterly accounting ratios.",
        bold_prefix="Regime Non-Additivity & SVB Dynamics: "
    )

    # ---------------------------------------------------------------------------
    # PART 6 – CONCLUSIONS, RESEARCH QUESTIONS & POLICY IMPLICATIONS [5 POINTS]
    # ---------------------------------------------------------------------------
    add_heading_1(doc, "PART 6 – CONCLUSIONS, RESEARCH QUESTIONS & POLICY IMPLICATIONS [5 POINTS]")

    add_heading_2(doc, "6.1 Explicit Direct Answers to the Professor's Three Research Questions")

    add_paragraph(
        doc,
        "Research Inquiry 1 (from Assignment Specification): How should four decades of bank reports be stored and processed on a laptop, and when would a Spark cluster be needed?",
        bold_prefix="Q1 Question: "
    )
    add_paragraph(
        doc,
        "Direct Empirical Answer to Q1: Four decades of historical quarterly Call Reports (1.68 million rows across 170 continuous quarters) should be stored exclusively as columnar Apache Parquet with Zstandard (zstd) compression, partitioned by reporting quarter. Parquet-zstd delivers a 2.95x physical compression ratio over raw CSV (143.9 MiB vs. 424.1 MiB) and accelerates sequential full-table scans by 21.82x (0.47s vs. 10.26s).\n\n"
        "For processing on a standard multi-core laptop, Polars Lazy API is overwhelmingly superior to both pandas and PySpark Local[*]. Polars transforms the 1.68M-row panel in 0.797 seconds with a 774 MiB memory footprint—outperforming single-threaded pandas (5.157s, 794 MiB) by 6.47x and PySpark Local[*] (14.757s, 1,013 MiB) by 18.52x. Scaling across 2x (3.35M rows) and 5x (8.39M rows), Polars processes the complete analytical workload in 2.464 seconds, while PySpark requires 31.514 seconds.\n\n"
        "A distributed Spark cluster is NOT required for historical Call Report modeling on a standard 16GB laptop. A distributed Spark cluster is justified if and only if: (1) Working dataset size exceeds single-node physical RAM (>64 GB), causing fatal memory swapping and OS kernel thrashing; (2) Data resides across distributed enterprise data lakes (Amazon S3, HDFS, Azure Data Lake) requiring petabyte-scale partition shuffles; (3) Analytical pipelines require real-time streaming integration with Apache Kafka brokers; or (4) Modeling pipelines utilize distributed cluster MLlib algorithms across multiple physical server nodes.",
        bold_prefix="Direct Answer to Q1: "
    )

    add_paragraph(
        doc,
        "Research Inquiry 2 (from Assignment Specification): What quality problems do the raw data contain, and how does the pipeline handle them without look-ahead bias?",
        bold_prefix="Q2 Question: "
    )
    add_paragraph(
        doc,
        "Direct Empirical Answer to Q2: The raw Call Report data contain three severe historical quality defects: (1) Historical schema drift where credit impairment variables like 30–89 day past due loans (P3ASSET) were structurally uncollected prior to 2001; (2) Regulatory accounting structural breaks, most notably Risk-Weighted Assets (RBCRWAJ) exhibiting a 100.0% structural zero rate prior to the 1990 Basel I enactment, and rising back to 36.4%–41.5% post-2020 under Community Bank Leverage Ratio (CBLR) simplified reporting; and (3) Exactly 5,631 post-exit zombie filing records across 62 unique failure CERTs where acquiring institutions or bridge banks continued filing receivership balance sheets under the original charter identifier.\n\n"
        "The pipeline eliminates lookahead bias through four strict architectural safeguards: (1) Purging all 5,631 post-closure zombie records using official FDIC receivership dates; (2) Establishing an absolute 1-year embargo quarantine across calendar year 2008 (33,039 valid observations, 176 unique failed banks) to prevent forward-looking distress signals from contaminating Test evaluation; (3) Computing all temporal lags and momentum features via an integer calendar quarter index (q_idx = year * 4 + quarter - 1) rather than sequential row shifts, setting gap transitions to null; and (4) Fitting all Winsorization percentiles, imputation medians, and robust scaling parameters strictly on the Development partition (1984–2007) and freezing them before transforming held-out Test data.",
        bold_prefix="Direct Answer to Q2: "
    )

    add_paragraph(
        doc,
        "Research Inquiry 3 (from Assignment Specification): Can the pipeline's output support an honestly validated early-warning model?",
        bold_prefix="Q3 Question: "
    )
    add_paragraph(
        doc,
        "Direct Empirical Answer to Q3: Yes. Evaluated strictly ONCE on the frozen out-of-time Test split (2009Q1–2025Q2; 386,964 valid labeled observations, 1,775 failure events, 500 unique failed bank charters), LightGBM calibrated under an empirical FDIC resolution loss ratio of 40.3:1 (median resolution loss = 20.17% of total assets; assumed examination cost CFP = 0.50% of assets) at frozen threshold tau* = 0.0201 captures 484 out of 500 unique failed banks (96.8% institutional recall) and 93.30% of distressed bank-quarters flagging only 1.78% of eligible held-out Test bank-quarter observations, cutting modeled expected supervisory examination loss by 59.7% relative to uncalibrated Logistic Regression (10,025.7 vs. 24,863.0 expected cost units) under the assumed loss function.\n\n"
        "Macroeconomic regime diagnostics reveal critical boundaries: the model was virtually clairvoyant during the credit-driven Great Financial Crisis (capturing 460 of 468 banks, 98.29%), but captured only 5 of 9 institutions (55.56%) during the 2023 regional banking turmoil. The collapse of Silicon Valley Bank was driven by unhedged interest rate duration mismatch and hyper-concentrated digital deposit flight occurring within 48 hours—dynamics that quarterly Call Reports cannot observe in real time.",
        bold_prefix="Direct Answer to Q3: "
    )

    add_heading_2(doc, "6.2 Comprehensive Systemic Limitations and Governance Principles")
    add_paragraph(
        doc,
        "In accordance with rigorous academic integrity standards, the following known limitations are formally disclosed:\n"
        "1. Workstation Hardware Boundary: Due to single-node workstation physical RAM constraints (16 GB), 10x synthetic scaling was not executed. Single-node superiority of Polars is proven up to 5x (8.39M rows); distributed Spark scaling requires a multi-node cluster or datasets exceeding physical RAM.\n"
        "2. Examination Cost Parameter Assumption: The examination cost parameter CFP = 0.005 * total assets is an assumed supervisory scenario benchmark, not an invoice audit identified from historical FDIC operational budgets.\n"
        "3. Lifecycle Event Adjudication: Exactly 29 conflicting historical CERTs with inst_end_date < failure_date (106 positive bank-quarters historically, 0 in Test) remain pending granular merger-registry matching. Unknown exits remain censored to avoid negative label corruption.\n"
        "4. High-Frequency Run Blindness: Quarterly Call Reports cannot capture viral, social-media-accelerated deposit runs occurring within hours (e.g., Silicon Valley Bank in March 2023).\n"
        "5. Model Governance (SR 11-7): Algorithmic risk alerts must serve as decision-support prioritization tools for on-site examination scheduling, not automated regulatory sanctioning mechanisms.",
        bold_prefix="Systemic Limitations: "
    )

    add_heading_2(doc, "6.3 Policy and Architectural Adaptation to the State Bank of Vietnam (SBV)")
    add_paragraph(
        doc,
        "Translating this early-warning framework to the Vietnamese banking sector under the State Bank of Vietnam (SBV — Ngan hang Nha nuoc Viet Nam) requires addressing four systemic structural differences:\n\n"
        "1. Regulatory Accounting Mapping: Commercial banks in Vietnam report under VAS and SBV circulars. Capital adequacy maps to Circular 41/2016/TT-NHNN (Basel II CAR >= 8.0%). Asset quality incorporates Circular 11/2021/TT-NHNN governing 5 debt classification tiers (No nhom 1–5). Internal controls align with Circular 13/2018/TT-NHNN. Liquidity limits enforce Circular 22/2019/TT-NHNN as amended by Circular 08/2020/TT-NHNN (capping short-term funds for medium/long loans at 30%). Debt rescheduling incorporates Circular 02/2023/TT-NHNN and Circular 06/2024/TT-NHNN.\n\n"
        "2. Event Adjudication (Special Control & 0-VND Compulsory Acquisitions): Commercial bank bankruptcy is avoided due to systemic stability priorities. Under the Law on Credit Institutions 2024 (No. 32/2024/QH15, effective July 1, 2024), regulatory intervention operates through Special Control (Kiem soat dac biet, e.g., SCB in 2022) or compulsory transfer (chuyen giao bat buoc 0 dong, as applied to CBBank, OceanBank, GPBank, DongABank). The target y_{i, t+4} must therefore detect entry into SBV Special Control rather than charter liquidation.\n\n"
        "3. Four-Tier Institutional Segmentation: Peer normalization must be calculated within four segmented tiers: (1) State-Owned Commercial Banks (SOCBs / Big 4: Vietcombank, BIDV, VietinBank, Agribank); (2) Large Private Joint-Stock Commercial Banks (> 300,000 billion VND assets); (3) Small Regional Joint-Stock Banks; and (4) Foreign Bank Branches and Joint Ventures.\n\n"
        "4. High-Frequency Telemetry Integration: To detect viral digital runs (akin to SCB in Oct 2022), the SBV must augment quarterly reports with daily clearing telemetry from NAPAS, weekly Open Market Operations (OMO) repos, and bi-weekly credit quota (room tin dung) metrics.\n\n"
        "Explicit Disclaimer: This supervisory architecture is proposed as an academic engineering concept and has not been executed on proprietary SBV data.",
        bold_prefix="Vietnamese Supervisory Adaptation: "
    )

    add_heading_2(doc, "6.4 Academic Integrity, Code Citation, and Generative AI Disclosure")
    add_paragraph(
        doc,
        "In compliance with academic integrity standards for BFT65B at the National Economics University, Generative AI (Google DeepMind Antigravity AI partner, Gemini 3.8 Flash) was utilized as an interactive co-auditor for debugging PySpark Local configurations, refactoring Polars expressions, compiling Word COM scripts, and drafting verification assertions. All data processing logic, econometric target formulations, cost ratio derivations, and analytical interpretations were conceived, audited, executed, and verified by the author.",
        bold_prefix="Academic Integrity & AI Disclosure: "
    )

    # ---------------------------------------------------------------------------
    # REFERENCES
    # ---------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_1(doc, "ACADEMIC & REGULATORY REFERENCES")

    refs = [
        ("Altman, E. I. (1968).", " Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. The Journal of Finance, 23(4), 589–609. https://doi.org/10.1111/j.1540-6261.1968.tb00843.x"),
        ("Basel Committee on Banking Supervision. (1988).", " International Convergence of Capital Measurement and Capital Standards (Basel I). Bank for International Settlements. https://www.bis.org/publ/bcbs04a.htm"),
        ("Basel Committee on Banking Supervision. (2006).", " Basel II: International Convergence of Capital Measurement and Capital Standards: A Revised Framework. Bank for International Settlements. https://www.bis.org/publ/bcbs128.htm"),
        ("Basel Committee on Banking Supervision. (2011).", " Basel III: A global regulatory framework for more resilient banks and banking systems. Bank for International Settlements. https://www.bis.org/publ/bcbs189.htm"),
        ("Cole, R. A., & Wu, Q. (2010).", " Predicting bank failures using a simple dynamic hazard model. Journal of Financial Stability, 6(4), 212–220. https://doi.org/10.1016/j.jfs.2010.02.001"),
        ("Demirgüç-Kunt, A., & Detragiache, E. (1998).", " The determinants of banking crises in developing and developed countries. IMF Staff Papers, 45(1), 81–109. https://doi.org/10.2307/3867330"),
        ("Federal Deposit Insurance Corporation. (1997).", " History of the Eighties: Lessons for the Future (Vol. 1: An Examination of the Banking Crises of the 1980s and Early 1990s). FDIC Division of Research and Statistics. Washington, D.C."),
        ("Federal Deposit Insurance Corporation. (2024).", " BankFind Suite: API Documentation and Historical Data Service. Federal Deposit Insurance Corporation. https://banks.data.fdic.gov/"),
        ("Federal Reserve System. (2011).", " SR Letter 11-7: Guidance on Model Risk Management. Board of Governors of the Federal Reserve System. Washington, D.C."),
        ("Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017).", " LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems (NeurIPS 2017), 30, 3146–3154."),
        ("National Assembly of Vietnam. (2024).", " Law on Credit Institutions No. 32/2024/QH15. Passed January 18, 2024; effective July 1, 2024. Hanoi, Vietnam."),
        ("Ohlson, J. A. (1980).", " Financial ratios and the probabilistic prediction of bankruptcy. Journal of Accounting Research, 18(1), 109–131. https://doi.org/10.2307/2490395"),
        ("Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011).", " Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830."),
        ("State Bank of Vietnam. (2016).", " Circular No. 41/2016/TT-NHNN: Regulating Capital Adequacy Ratio for Commercial Banks and Foreign Bank Branches. Issued December 30, 2016. Hanoi, Vietnam."),
        ("State Bank of Vietnam. (2018).", " Circular No. 13/2018/TT-NHNN: Regulating Internal Control Systems of Commercial Banks and Foreign Bank Branches. Issued May 18, 2018. Hanoi, Vietnam."),
        ("State Bank of Vietnam. (2019).", " Circular No. 22/2019/TT-NHNN: Regulating Limits and Prudential Ratios in Operations of Banks and Foreign Bank Branches. Issued November 15, 2019. Hanoi, Vietnam."),
        ("State Bank of Vietnam. (2020).", " Circular No. 08/2020/TT-NHNN: Amending and Supplementing Circular No. 22/2019/TT-NHNN. Issued August 14, 2020. Hanoi, Vietnam."),
        ("State Bank of Vietnam. (2023).", " Circular No. 02/2023/TT-NHNN: Regulating Debt Rescheduling and Retention of Debt Category. Issued April 23, 2023. Hanoi, Vietnam."),
        ("State Bank of Vietnam. (2024).", " Circular No. 06/2024/TT-NHNN: Amending and Supplementing Circular No. 02/2023/TT-NHNN. Issued June 18, 2024. Hanoi, Vietnam."),
        ("Wheelock, D. C., & Wilson, P. W. (2000).", " Why do banks disappear? The determinants of U.S. bank failures and acquisitions. The Review of Economics and Statistics, 82(1), 127–138. https://doi.org/10.1162/003465300558560")
    ]
    for author, citation in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(2.5)
        p.paragraph_format.line_spacing = 1.15
        ra = p.add_run(author)
        ra.font.name = "Times New Roman"
        ra.font.size = Pt(8.5)
        ra.font.bold = True
        ra.font.color.rgb = NAVY
        rc = p.add_run(citation)
        rc.font.name = "Times New Roman"
        rc.font.size = Pt(8.5)
        rc.font.color.rgb = CHARCOAL

    # ---------------------------------------------------------------------------
    # TECHNICAL APPENDICES
    # ---------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_1(doc, "TECHNICAL APPENDICES (APPENDICES A TO E)")

    add_heading_2(doc, "Appendix A: Regulatory Capital Accounting Transition (Basel I, Basel II, Basel III, CBLR)")
    add_paragraph(
        doc,
        "Prior to 1990Q1, regulatory reporting did not require risk-weighted assets (RBCRWAJ), producing 100.0% structural zeros in historical Call Reports. Capital adequacy was evaluated solely via raw leverage (Equity to Assets). With the legal enactment of the Basel I Accord in 1990, capital adequacy was evaluated via Tier 1 Risk-Based Capital (RBC1AAJ) and Total Risk-Based Capital relative to Risk-Weighted Assets. Under Basel II (2006+) and Basel III (2015+), Common Equity Tier 1 (CET1) and dynamic risk-weighting schedules were established. In 2020, the Community Bank Leverage Ratio (CBLR) framework allowed qualifying community banking institutions (< $10 billion in assets with leverage ratio >= 9.0%) to opt out of risk-weighted calculations, causing structural zero rates for RBCRWAJ to climb back to 36.4%–41.5%. Table A.1 summarizes this regulatory timeline:",
        bold_prefix="Accounting Timeline: "
    )

    app_a_headers = ["Regulatory Era", "Calendar Scope", "Key Capital Metrics Mandated", "Observed Structural Zero Rate", "Modeling Treatment & Handling"]
    app_a_rows = [
        ["Pre-Basel I Era", "1984Q1–1989Q4", "EQ / ASSET (Book Leverage)", "100.0% for RBCRWAJ; 17.6% for RBC1AAJ", "Engineered is_pre_basel = 1; zero-safe ratios"],
        ["Basel I Accord", "1990Q1–1995Q4", "Tier 1 & Total Risk-Based Capital", "0.3% for RBCRWAJ; 0.2% for RBC1AAJ", "Mandatory RWA reporting; baseline standard"],
        ["Basel I/II Expansion", "1996Q1–2007Q4", "Market Risk & Standardized Basel II", "0.2% for RBCRWAJ; 0.2% for RBC1AAJ", "Stable longitudinal reporting across panel"],
        ["Basel III & Post-GFC", "2008Q1–2019Q4", "CET1, Capital Conservation Buffers", "0.2% for RBCRWAJ; 0.3% for RBC1AAJ", "High compliance across commercial banks"],
        ["CBLR Simplified Era", "2020Q1–2026Q2", "CBLR Option (Leverage >= 9.0%)", "36.4%–41.5% for RBCRWAJ", "Opt-out for community banks; tracked via _isna"]
    ]
    add_styled_table(
        doc,
        headers=app_a_headers,
        data_rows=app_a_rows,
        col_widths=[1.3, 1.1, 1.5, 1.2, 1.4],
        caption="Table A.1: Longitudinal Regulatory Capital Reporting Eras and Missingness Handling Standards",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_heading_2(doc, "Appendix B: Multi-Engine Technical Specifications and Environment Topology")
    add_paragraph(
        doc,
        "All computational experiments were conducted on a single multi-core workstation. Environment specifications: (1) Processor: AMD Ryzen 7 (8 physical cores, 16 logical hardware execution threads at 3.80 GHz); (2) Memory: 16.0 GB DDR4 physical RAM; (3) Storage: 1.0 TB NVMe PCIe M.2 Solid State Drive; (4) Operating System: Microsoft Windows 11 Enterprise (Build 22631); (5) Python Runtime: CPython 3.11.9 (observed research environment); (6) Java Runtime: OpenJDK 17.0.21.1 (HotSpot 64-Bit Server VM); (7) Core Libraries: Polars 2.1.0 (Rayon multithreading), pandas 2.2.3 with PyArrow 12.0.1 backend, PySpark 3.5.3 (Spark Local[*] with 8 shuffle partitions and 4 GB JVM driver memory), scikit-learn 1.9.1, LightGBM 4.7.0, python-docx 1.2.0, PyMuPDF 1.24.",
        bold_prefix="Hardware & Environment Architecture: "
    )

    add_heading_2(doc, "Appendix C: Mathematical Formulation of 30 Point-in-Time CAMELS Features")
    add_paragraph(
        doc,
        "Table C.1 provides the complete mathematical definitions, CAMELS categorization, and Development-only baseline statistics (Median, Mean, Std) for all 30 active base predictors stored in artifacts/features/preprocessor_dev_params.json:",
        bold_prefix="Feature Store Formulas: "
    )

    # Load preprocessor params
    prep_params_path = Path("artifacts/features/preprocessor_dev_params.json")
    if not prep_params_path.exists():
        prep_params_path = Path("artifacts/stageB/baseline/feature_params/preprocessor_dev_params.json")
    with open(prep_params_path, encoding="utf-8") as f:
        prep_params = json.load(f)

    app_c_headers = ["Feature", "CAMELS", "Mathematical Formulation", "Dev Median", "Dev Mean", "Dev Std", "Supervisory Rationale"]
    formulas_c = {
        "cap_ratio": ("C", "EQ / ASSET", "Core leverage buffer"),
        "rbc_tier1": ("C", "RBC1AAJ (reported)", "Basel Tier 1 risk-weighted ratio"),
        "rbc_total": ("C", "RBCRWAJ (reported)", "Basel Total risk-weighted ratio"),
        "neg_equity_flag": ("C", "(EQ < 0)", "Direct technical insolvency flag"),
        "is_pre_basel": ("C", "(REPDTE < '19900331')", "Regulatory regime structural break"),
        "npl_ratio": ("A", "NCLNLS / LNLSNET", "Non-performing loan burden"),
        "reserve_coverage": ("A", "LNATRES / NCLNLS", "Provision buffer over impaired loans"),
        "nonperf_asset_ratio": ("A", "(P3ASSET+P9+NA)/ASSET", "Comprehensive impaired assets share"),
        "ore_ratio": ("A", "ORE / ASSET", "Foreclosed real estate inventory"),
        "re_loan_share": ("A", "LNRE / LNLSGR", "Real estate lending concentration"),
        "ci_loan_share": ("A", "LNCI / LNLSGR", "Commercial & industrial loan share"),
        "nonix_asset_ratio": ("M", "NONIX / ASSET", "Operating expense overhead burden"),
        "roa": ("E", "ROA (reported)", "Return on assets profitability"),
        "roe": ("E", "ROE (reported)", "Return on book equity"),
        "nimy": ("E", "NIMY (reported)", "Net interest margin yield"),
        "roa_lag1": ("E", "roa(t-1Q)", "Preceding quarter profitability"),
        "roa_lag4": ("E", "roa(t-4Q)", "Annual baseline profitability"),
        "roa_diff_qoq": ("E", "roa(t) - roa(t-1Q)", "Quarterly earnings momentum"),
        "roa_std_4q": ("E", "rolling_std(roa, 4Q)", "Earnings stream volatility"),
        "nimy_std_4q": ("E", "rolling_std(nimy, 4Q)", "Interest margin volatility"),
        "liq_asset_ratio": ("L", "(CHBAL + SC) / ASSET", "Liquid assets to total assets"),
        "liq_dep_ratio": ("L", "(CHBAL + SC) / DEP", "Liquid reserves to deposit base"),
        "ldr": ("L", "LNLSNET / DEP", "Loan-to-deposit structural ratio"),
        "brokered_dep_ratio": ("L", "BRO / DEP", "Volatile wholesale funding share"),
        "log_asset": ("Size", "ln(ASSET)", "Institution scale & franchise size"),
        "asset_growth_qoq": ("Growth", "ASSET(t)/ASSET(t-1) - 1", "Short-term balance sheet momentum"),
        "asset_growth_yoy": ("Growth", "ASSET(t)/ASSET(t-4) - 1", "Annual balance sheet expansion"),
        "cap_zscore_q": ("Peer", "(cap - mean_q) / std_q", "Peer-relative capital position"),
        "roa_zscore_q": ("Peer", "(roa - mean_q) / std_q", "Peer-relative earnings strength"),
        "npl_zscore_q": ("Peer", "(npl - mean_q) / std_q", "Peer-relative credit impairment")
    }

    app_c_rows = []
    for feat, (cat, form, desc) in formulas_c.items():
        p = prep_params.get(feat, {"median": 0.0, "mean": 0.0, "std": 1.0})
        app_c_rows.append([
            feat,
            cat,
            form,
            f"{p['median']:.4f}",
            f"{p['mean']:.4f}",
            f"{p['std']:.4f}",
            desc
        ])

    add_styled_table(
        doc,
        headers=app_c_headers,
        data_rows=app_c_rows,
        col_widths=[1.2, 0.5, 1.4, 0.7, 0.7, 0.7, 1.3],
        caption="Table C.1: Master Active CAMELS Feature Store Dictionary and Development Baseline Parameters",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_heading_2(doc, "Appendix D: Time-Series Expanding Cross-Validation Partition Dates")
    add_paragraph(
        doc,
        "Expanding CV partitions on Development (1984Q1–2007Q4) with fold-local feature availability selection:\n"
        "• Fold 1: Training Window 1984Q1–1997Q4 (14 years; 29 Train-available features, nonperf_asset_ratio excluded), Purge Buffer 1998Q1–1998Q4 (4 quarters), Validation Window 1999Q1–2002Q4 (152,958 bank-quarters, 104 failure events).\n"
        "• Fold 2: Training Window 1984Q1–2001Q4 (18 years; 30 Train-available features), Purge Buffer 2002Q1–2002Q4 (4 quarters), Validation Window 2003Q1–2005Q4 (105,955 bank-quarters, 20 failure events).\n"
        "• Fold 3: Training Window 1984Q1–2004Q4 (21 years; 30 Train-available features), Purge Buffer 2005Q1–2005Q4 (4 quarters), Validation Window 2006Q1–2007Q4 (67,468 bank-quarters, 55 failure events).\n"
        "• Held-Out Test: Training Window 1984Q1–2007Q4 (24 years; 30 Dev-available features), Quarantine Embargo 2008Q1–2008Q4 (4 quarters), Final Out-of-Time Test Evaluation 2009Q1–2025Q2 (16.5 years: 386,964 bank-quarters, 1,775 failure events, 500 unique failed bank charters).",
        bold_prefix="Partition Breakdown: "
    )

    add_heading_2(doc, "Appendix E: Machine Learning Hyperparameter Grids and Tuning Protocols")
    add_paragraph(
        doc,
        "Hyperparameter specifications (predefined baseline configurations evaluated without automated grid search):\n"
        "1. Logistic Regression: L2 penalty (Ridge), regularization strength C = 0.5, solver = 'lbfgs', maximum iterations = 500, tolerance = 1e-4, fit_intercept = True, random_state = 42.\n"
        "2. LightGBM Classifier: boosting_type = 'gbdt', objective = 'binary', n_estimators = 300, learning_rate = 0.03, num_leaves = 31, max_depth = -1, min_child_samples = 100, subsample = 0.8, colsample_bytree = 0.8, subsample_for_bin = 50000, random_state = 42, n_jobs = -1, class_weight = None (loss-informed thresholding applied post-prediction).\n"
        "3. PySpark MLlib Logistic Regression: maxIter = 25, regParam = 0.01, featuresCol = 'features', labelCol = 'label' (native areaUnderPR = 0.5547; scikit-learn AP = 0.5699).",
        bold_prefix="Hyperparameter Specification: "
    )

    # Save DOCX
    out_dir = Path("deliverables")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_docx = out_dir / "DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx"
    doc.save(str(out_docx))
    print(f"Successfully generated expanded submission DOCX at: {out_docx} (size: {out_docx.stat().st_size:,} bytes)")
    return out_docx


if __name__ == "__main__":
    build_submission_document()
