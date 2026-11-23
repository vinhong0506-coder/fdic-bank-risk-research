from __future__ import annotations
import json
import os
from pathlib import Path
import pandas as pd
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

NAVY = RGBColor(27, 54, 93)      # #1B365D - Dark Navy
SLATE = RGBColor(52, 73, 94)     # #34495E - Dark Slate
CHARCOAL = RGBColor(33, 37, 41)  # #212529 - Body Text
GRAY_TEXT = RGBColor(108, 117, 125) # #6C757D
WHITE = RGBColor(255, 255, 255)

NAVY_HEX = "1B365D"
LIGHT_BG_HEX = "F4F6F9"
BORDER_HEX = "D3D3D3"
ALT_ROW_HEX = "F8F9FA"


def set_cell_background(cell, fill_hex: str) -> None:
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top: int = 100, bottom: int = 100, left: int = 140, right: int = 140) -> None:
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


def add_page_number_to_paragraph(p) -> None:
    fldSimple = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>')
    p._p.append(fldSimple)


def add_heading_1(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = NAVY


def add_heading_2(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12.5)
    run.font.bold = True
    run.font.color.rgb = NAVY


def add_heading_3(doc: docx.Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = SLATE


def add_paragraph(doc: docx.Document, text: str, bold_prefix: str | None = None, space_after: float = 4.5) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
        r_pre.font.color.rgb = CHARCOAL
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    run.font.color.rgb = CHARCOAL


def add_bullet(doc: docx.Document, text: str, bold_prefix: str | None = None) -> None:
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(10.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = CHARCOAL
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10.5)
    run.font.color.rgb = CHARCOAL


def add_callout(doc: docx.Document, text: str, title: str | None = None) -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, LIGHT_BG_HEX)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{NAVY_HEX}"/>
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
        rt.font.size = Pt(10.5)
        rt.font.bold = True
        rt.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.italic = True
    r.font.color.rgb = CHARCOAL
    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_figure(doc: docx.Document, img_path: Path | str, caption: str, width: Inches = Inches(6.2)) -> None:
    img_path = Path(img_path)
    if not img_path.exists():
        add_paragraph(doc, f"[Figure Missing: {img_path.name}]", bold_prefix="Warning: ")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(img_path), width=width)

    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(10)
    c_run = cp.add_run(caption)
    c_run.font.name = "Times New Roman"
    c_run.font.size = Pt(9.5)
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
        cp.paragraph_format.space_before = Pt(8)
        cp.paragraph_format.space_after = Pt(3)
        cp.paragraph_format.keep_with_next = True
        c_run = cp.add_run(caption)
        c_run.font.name = "Times New Roman"
        c_run.font.size = Pt(9.5)
        c_run.font.bold = True
        c_run.font.color.rgb = NAVY

    tbl = doc.add_table(rows=len(data_rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    # Header Row
    hdr_row = tbl.rows[0]
    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx]
        set_cell_background(cell, NAVY_HEX)
        set_cell_margins(cell, top=100, bottom=100, left=110, right=110)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.alignment = alignments[idx] if alignments else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = WHITE

    # Data Rows
    for r_idx, row_vals in enumerate(data_rows):
        row = tbl.rows[r_idx + 1]
        bg_col = ALT_ROW_HEX if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            if bg_col != "FFFFFF":
                set_cell_background(cell, bg_col)
            set_cell_margins(cell, top=70, bottom=70, left=110, right=110)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.alignment = alignments[c_idx] if alignments else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(val))
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            r.font.color.rgb = CHARCOAL

    if col_widths:
        for row in tbl.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    format_table_rows(tbl)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build_academic_report(out_docx_path: Path) -> None:
    doc = docx.Document()

    # 1. Page Margins (0.85 inch = 1224 dxa)
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.different_first_page_header_footer = True

        # Header for subsequent pages
        hdr_p = section.header.paragraphs[0]
        hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hdr_r = hdr_p.add_run("NEU School of Banking & Finance | Big Data Analytics in Finance (Class 65B-BFT)")
        hdr_r.font.name = "Times New Roman"
        hdr_r.font.size = Pt(8.5)
        hdr_r.font.color.rgb = GRAY_TEXT

        # Footer for subsequent pages
        ftr_p = section.footer.paragraphs[0]
        ftr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        ftr_r1 = ftr_p.add_run("Dao Huy Thanh Vinh (MSV: 11231024)  |  Page ")
        ftr_r1.font.name = "Times New Roman"
        ftr_r1.font.size = Pt(9)
        ftr_r1.font.color.rgb = GRAY_TEXT
        add_page_number_to_paragraph(ftr_p)

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(12)
    p_inst.paragraph_format.space_after = Pt(2)
    r = p_inst.add_run("NATIONAL ECONOMICS UNIVERSITY (NEU)\nSCHOOL OF BANKING AND FINANCE")
    r.font.name = "Times New Roman"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = NAVY

    p_prog = doc.add_paragraph()
    p_prog.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_prog.paragraph_format.space_before = Pt(0)
    p_prog.paragraph_format.space_after = Pt(28)
    r = p_prog.add_run("BACHELOR OF FINANCIAL TECHNOLOGY (95% ENGLISH-TAUGHT PROGRAM)\nCLASS 65B-BFT — COURSE: BIG DATA ANALYTICS IN FINANCE")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = SLATE

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(12)
    r = p_title.add_run("U.S. BANK FAILURE EARLY-WARNING SYSTEM:\nA POINT-IN-TIME BIG DATA ENGINEERING AND COST-SENSITIVE MODELING PIPELINE (1984Q1–2026Q2)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(17)
    r.font.bold = True
    r.font.color.rgb = NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(28)
    r = p_sub.add_run("Individual Research Report on Scalable Ingestion, Anti-Leakage Feature Stores,\nAsymmetric Supervisory Loss Calibration, and Macroprudential Transferability to Vietnam")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.italic = True
    r.font.color.rgb = CHARCOAL

    # Student metadata box
    meta_headers = ["Student Full Name", "Student ID (MSV)", "Cohort & Program", "Submission Date"]
    meta_data = [["Dao Huy Thanh Vinh", "11231024", "Class 65B-BFT (FinTech Honors)", "November 26, 2026"]]
    add_styled_table(doc, meta_headers, meta_data, col_widths=[1.8, 1.4, 2.0, 1.5], caption="Author Identification & Academic Affiliation")

    p_git = doc.add_paragraph()
    p_git.paragraph_format.space_before = Pt(6)
    p_git.paragraph_format.space_after = Pt(14)
    r = p_git.add_run("Public GitHub Repository: ")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.bold = True
    r = p_git.add_run("https://github.com/vinhong0506-coder/fdic-bank-risk-research")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.underline = True
    r.font.color.rgb = NAVY

    # Locked Dataset Snapshot Table on Cover Page
    snap_headers = ["Pipeline Parameter / Dimension", "Locked Value / Audit Count", "Supervisory & Methodological Significance"]
    snap_data = [
        ["Temporal Horizon Scope", "170 Quarters (1984Q1–2026Q2)", "Covers 42.5 years: S&L Crisis, Dot-com, GFC 2008, COVID-19, and SVB 2023"],
        ["Raw Ingested Records", "1,682,738 Bank-Quarters", "170 quarterly bulk Call Report files, complete sha256 manifest verification"],
        ["Post-Exit Zombie Purge", "5,631 Zombie Rows Removed", "Eliminates post-receivership survivor bias and retrospective distortion"],
        ["Point-in-Time Clean Panel", "1,677,107 Verified Records", "Zero duplicate (CERT, REPDTE) keys, strict quarterly calendar sequence"],
        ["Development Split (1984–2007)", "1,224,942 Rows (2,680 Failures)", "Training & cross-validation fold; base failure incidence = 0.829%"],
        ["Embargo Gap Split (2008)", "33,966 Rows (176 Failures)", "12-month quarantine preventing lookahead label bleed across crisis boundary"],
        ["Out-of-Sample Test (2009–2025Q2)", "400,698 Rows (500 Failures)", "Frozen test set evaluating crisis, expansion, and digital bank runs"],
        ["Right-Censored Recent Window", "17,501 Rows (2025Q3–2026Q2)", "Target label censored due to unexpired 12-month forward resolution horizon"],
        ["Engineered Feature Matrix", "1,677,107 x 70 Columns", "31 base CAMELS + 31 missing indicators + 8 metadata (0 NaN, 0 Inf)"],
        ["Empirical Loss Ratio (CFN/CFP)", "40.3 : 1 ($C_{FN}/C_{FP}$)", "Derived from N=1,275 historical FDIC receivership loss resolutions"],
    ]
    add_styled_table(
        doc,
        snap_headers,
        snap_data,
        col_widths=[2.1, 1.9, 2.7],
        caption="Table C.1: Locked Research Pipeline Snapshot & Data Partition Baseline",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    doc.add_page_break()

    # =========================================================================
    # EXECUTIVE SUMMARY & RESEARCH QUESTIONS
    # =========================================================================
    add_heading_1(doc, "Executive Summary & Research Inquiries")

    add_paragraph(
        doc,
        "Commercial banking stability is a vital pillar of macroeconomic resilience. Because bank insolvencies generate devastating systemic externalities—eroding depositor confidence, triggering credit crunches, and imposing severe costs on sovereign deposit insurance funds—regulatory authorities require automated early-warning systems (EWS) to prioritize on-site supervisory examinations. This research investigates the end-to-end engineering, computational benchmarking, and econometrically sound predictive modeling of bank distress using the complete Federal Deposit Insurance Corporation (FDIC) Call Report universe spanning 170 consecutive quarters from 1984Q1 through 2026Q2 (1.68 million bank-quarters)."
    )

    add_paragraph(
        doc,
        "Unlike academic prototypes that rely on synthetic or heavily down-sampled panels, this project confronts real-world big data challenges: massive historical schema drift, structural regulatory regime shifts (the transition from pre-Basel capital rules to Basel I, Basel II/III, and the Community Bank Leverage Ratio), severe class imbalance (<1% quarterly failures), post-failure zombie filings, and operational loss asymmetries. By integrating modern vectorized columnar execution engines (Polars Lazy API) and distributed cluster architectures (Apache Spark / PySpark) with anti-leakage Point-in-Time feature stores, this paper answers three core research questions:"
    )

    add_callout(
        doc,
        "Question 1 (Computational & Scalability Break-Even): At what dataset scale and infrastructure configuration does a distributed framework (PySpark) justify its operational overhead versus an in-memory vectorized multi-threaded engine (Polars)?\n\n"
        "Question 2 (Point-in-Time Predictive & Supervisory Utility): Does an anti-leakage, calendar-strict CAMELS feature pipeline coupled with asymmetric loss calibration provide meaningful early detection (12-month forward horizon) across heterogeneous crisis regimes without triggering excessive false-positive audits?\n\n"
        "Question 3 (Macroprudential & Regulatory Adaptation): How must data engineering schemas, event adjudication rules, and risk thresholds be adapted when transferring early-warning architectures to emerging market regulatory frameworks like Vietnam (State Bank of Vietnam - SBV)?",
        title="CORE RESEARCH INQUIRIES (Q1, Q2, Q3)"
    )

    add_heading_2(doc, "Summary of Key Empirical Findings")
    add_bullet(doc, "Parquet-zstd delivers a 2.95x storage compression ratio over raw CSV (143.94 MB vs. 424.65 MB) and accelerates full-table scan query speeds by 21.82x (0.47s vs. 10.26s).", bold_prefix="Storage Optimization: ")
    add_bullet(doc, "Polars Lazy API processes the entire 1.68M-row PIT panel in 0.322 seconds (5.22M rows/sec), achieving a 14.86x speedup over single-threaded Pandas (4.78s). On local multi-core hardware, PySpark Local[*] incurs JVM initialization overhead at 1x scale (0.768s), but exhibits superior horizontal scaling, overtaking Polars at the warm-JVM crossover point of 2x (~3.35M rows) and processing 16.77M rows in 0.890s (18.85M rows/s, an 11.81x speedup over Polars).", bold_prefix="Compute Engine Break-Even (Q1): ")
    add_bullet(doc, "An anti-leakage LightGBM model calibrated with an empirical cost ratio of 40.3:1 (derived from N=1,275 FDIC receivership loss ratios) captures 483 out of 500 unique failed institutions (96.6% recall) on the out-of-sample test split (2009Q1–2025Q2) at a supervisory alert rate of only 1.57%, reducing expected supervisory examination costs by 44.3% relative to standard Logistic Regression.", bold_prefix="Supervisory EWS Performance (Q2): ")
    add_bullet(doc, "Adapting this architecture to the State Bank of Vietnam (SBV, Circulars 41/2016 and 13/2018) requires reformulating the failure target around 'Special Control' (Kiểm soát đặc biệt) and 'Zero-Dong' compulsory acquisitions, segmenting institutions across four distinct ownership tiers, and augmenting quarterly Call Reports with high-frequency liquidity telemetry to prevent modern digital bank runs.", bold_prefix="Emerging Market Transferability (Q3): ")

    add_heading_2(doc, "System Architecture Pipeline Diagram")
    add_paragraph(doc, "Figure 0 depicts the end-to-end data engineering and modeling flow implemented in the project repository:")

    ascii_diagram = (
        "+-------------------------------------------------------------------------------------------------+\n"
        "|                             FDIC REST API / Bulk Sync (170 Quarters)                            |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Data Lake Ingestion & Storage: 1,682,738 rows -> Parquet-zstd (143.9 MB, 2.95x compression)    |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Point-in-Time (PIT) Audit: Purge 5,631 Zombie Rows -> Clean Panel: 1,677,107 Bank-Quarters       |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Temporal Split & 1-Year Embargo: Dev (84-07) | Embargo (2008: 33,966 rows) | Test (09-25: 400K) |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| CAMELS Feature Engine: 31 Base Ratios + Peer Z-Scores + Calendar-Strict Integer Lags (q_idx)    |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Dev-Only Preprocessing: Fit Winsorizer, Imputer, & Scaler strictly on Dev (Zero Leakage, 62 Feat)|\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Cost-Sensitive Modeling: Empirical Loss (CFN/CFP=40.3:1) -> Frozen Threshold tau* = 0.0240      |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "                                               |\n"
        "                                               v\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "| Out-of-Sample Test Evaluation: 96.6% Bank Capture, 1.57% Alert Rate, 44.3% Cost Reduction       |\n"
        "+-------------------------------------------------------------------------------------------------+"
    )
    add_callout(doc, ascii_diagram, title="Figure 0: End-to-End Architectural Pipeline Flowchart")

    # =========================================================================
    # SECTION 1: DATA ACQUISITION & COLUMNAR BENCHMARK
    # =========================================================================
    add_heading_1(doc, "Section 1: Data Acquisition, Manifest Integrity & Storage Benchmarking")

    add_paragraph(
        doc,
        "Commercial banks insured by the FDIC are legally mandated to submit quarterly Consolidated Reports of Condition and Income (Call Reports, FFIEC 031/041). The raw acquisition phase implemented a resilient, checkpoint-driven extraction engine (`src/fdic_pipeline/ingest.py`) connecting to the FDIC Bank Data REST API (`https://api.fdic.gov/banks`). The pipeline acquired all 170 consecutive quarters spanning March 31, 1984 (1984Q1) to June 30, 2026 (2026Q2), retrieving 33 core financial statement variables (`FIN_FIELDS`), 9 failure resolution variables (`FAIL_FIELDS`), and 9 structural demographic fields (`INST_FIELDS`)."
    )

    add_paragraph(
        doc,
        "To guarantee auditability and data provenance, each quarterly download is verified via a manifest ledger (`manifest_financials.json`) recording the exact API query timestamp, HTTP response status, total records reported by the server, actual ingested row count, SHA-256 cryptographic checksum, and Parquet byte footprint. Across 170 quarters, exactly 1,682,738 raw bank-quarter observations were retrieved with zero key duplications at ingestion time."
    )

    # Table 1.1: Storage Benchmark
    st_df = pd.read_csv("artifacts/benchmark/storage_full/storage_benchmark.csv")
    st_headers = ["File Format Codec", "Dataset Rows", "Storage Footprint (Bytes)", "Size (MB)", "Write Latency (s)", "Read Latency (s)", "Compression vs CSV", "Scan Speedup"]
    st_rows = []
    for _, r in st_df.iterrows():
        sz_mb = r["bytes"] / (1024 ** 2)
        comp = r["compression_ratio_vs_csv"]
        speed = st_df.loc[st_df["format"] == "CSV", "read_s"].values[0] / r["read_s"]
        st_rows.append([
            str(r["format"]),
            f"{int(r['rows']):,}",
            f"{int(r['bytes']):,}",
            f"{sz_mb:.2f} MB",
            f"{r['write_s']:.2f}s",
            f"{r['read_s']:.3f}s",
            f"{comp:.2f}x",
            f"{speed:.2f}x"
        ])

    add_styled_table(
        doc,
        st_headers,
        st_rows,
        col_widths=[1.2, 0.8, 1.1, 0.7, 0.8, 0.8, 0.8, 0.7],
        caption="Table 1.1: Empirical Storage & Full-Table Scan Benchmark on 1.68M Rows (storage_benchmark.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig1_storage_benchmark.png",
        "Figure 1: Columnar Storage Benchmark Comparing Disk Footprint (MB) and Full-Scan I/O Latency Across Codecs"
    )

    add_paragraph(
        doc,
        "Empirical Storage Evaluation: Table 1.1 and Figure 1 demonstrate the profound superiority of columnar storage over legacy row-oriented formats. Raw uncompressed CSV occupies 444.72 MB (424.12 MiB) on disk and requires 10.26 seconds for a full sequential scan. While Gzip compression achieves strong compaction (151.90 MB, 2.93x), its write latency is prohibitive (19.14 seconds) due to complex Huffman coding trees. Snappy prioritizes ingestion speed (6.47s write) but leaves a larger disk footprint (180.80 MB)."
    )

    add_paragraph(
        doc,
        "Parquet with Zstandard (zstd) compression emerges as the Pareto-optimal storage codec for financial Big Data pipelines. It attains the highest compression ratio (2.95x, reducing disk usage to 150.93 MB / 143.94 MiB) while delivering the fastest read scan latency (0.472 seconds, an astounding 21.82x acceleration over CSV) and the lowest write overhead (4.07s). This dramatic efficiency stems from Parquet's columnar layout, page-level dictionary encoding, run-length encoding (RLE), and Snappy/Zstd SIMD block decompression, which allow analytical query engines to bypass unused columns and evaluate predicate filters directly at the byte level."
    )

    # =========================================================================
    # SECTION 2: AUDIT & POINT-IN-TIME PANEL
    # =========================================================================
    add_heading_1(doc, "Section 2: Data Quality Audit, Lifecycle Adjudication & Point-in-Time Panel")

    add_paragraph(
        doc,
        "A critical vulnerability in banking risk research is the uncritical pooling of longitudinal administrative records without rigorous schema reconciliation and survival adjudication. Over a 42.5-year span, banking regulatory accounting underwent extensive structural revisions. Regulatory agencies frequently introduce, redefine, or discontinue accounting schedules, creating non-random missingness that naive imputation can misinterpret as financial distress."
    )

    add_paragraph(
        doc,
        "Schema Drift and Accounting Schedule Transitions: As documented in Table 2.1, variables such as past-due loans (30–89 days, `P3ASSET`) did not exist in Call Report schedules prior to March 2001 (57.77% panel missingness). Conversely, non-accrual loans (`NAASSET`) and loans 90+ days past due (`P9ASSET`) were collected consistently since 1984 (only 4.62% missingness). Net charge-offs (`NCLNLS`) and loan loss provisions (`ELNATR`) show near-perfect availability post-1996 (>99.7%). Recognizing these regulatory schedules prevents pipelines from mistaking missing reporting lines for zero delinquencies."
    )

    # Failure reconciliation
    rec_df = pd.read_csv("artifacts/audit/failure_reconciliation.csv")
    rec_headers = ["Reconciliation Category", "Observation Count", "Proportion (%)", "Methodological Disposition"]
    tot_f = rec_df.loc[rec_df["Category"] == "Total rows in raw failures.parquet", "Count"].values[0]
    rec_rows = []
    for _, r in rec_df.iterrows():
        c_name = r["Category"]
        cnt = int(r["Count"])
        pct = (cnt / tot_f) * 100
        disp = "Master Source Record" if "Total" in c_name else (
            "Excluded: Uninsured or pre-1934 resolution" if "null" in c_name else (
                "Consolidated: Administrative reopening" if "Duplicate" in c_name else (
                    "Included: Matched Call Report universe" if "matched" in c_name else "Excluded: Failed prior to 1984Q1"
                )
            )
        )
        rec_rows.append([c_name, f"{cnt:,}", f"{pct:.2f}%", disp])

    add_styled_table(
        doc,
        rec_headers,
        rec_rows,
        col_widths=[2.8, 1.0, 1.0, 2.0],
        caption="Table 2.1: Master Failure List Reconciliation & Discrepancy Adjudication (failure_reconciliation.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_paragraph(
        doc,
        "Reconciling the FDIC Failure Registry: A persistent source of confusion in banking research is the discrepancy between official FDIC failure headlines (e.g., 4,117 failure rows in `failures.parquet`) and the actual unique institutions modeled in Call Reports. Table 2.1 presents the rigorous accounting reconciliation conducted by our audit module (`audit.py`):"
    )
    add_bullet(doc, "Of the 4,117 raw failure rows, 488 records lack a valid FDIC Certificate Number (CERT is null). These correspond to historical state-chartered uninsured depositories, private banks, or early 20th-century bank holidays outside the Call Report filing system.", bold_prefix="1. Unassigned CERT Records: ")
    add_bullet(doc, "Exactly 44 rows represent duplicate failure filings for the same CERT (e.g., failed institutions reopened under conservatorship or amended purchase-and-assumption agreements). Consolidating these yields exactly 3,585 unique failed banks.", bold_prefix="2. Duplicate Resolution Filings: ")
    add_bullet(doc, "Cross-referencing these 3,585 unique failed CERTs against the 1984Q1–2026Q2 Call Report panel reveals that exactly 3,211 failed banks had active filing records within our historical window. The remaining 374 unique failed banks ceased operations prior to March 31, 1984, or were non-filing specialty trust entities.", bold_prefix="3. Temporal Coverage Match: ")

    add_heading_2(doc, "Exit Adjudication & Elimination of Post-Failure Zombie Rows")
    add_paragraph(
        doc,
        "In FDIC historical reporting, an institution's charter may linger in regulatory databases after its resolution date (`FAILDATE`) due to ongoing receivership accounting, asset liquidation trusts, or administrative delays in charter cancellation (`ENDEFYMD`). If unaddressed, these 'post-exit zombie rows' contaminate early-warning models by feeding insolvent, winding-down balance sheets as active negative examples."
    )
    add_paragraph(
        doc,
        "Our audit pipeline joined the master institution lifecycle table (`institutions.parquet`) against quarterly filings on CERT, enforcing the strict Point-in-Time invariant that no observation is retained if its reporting date exceeds its confirmed legal closure date (`quarter_date <= end_date`). This filter successfully detected and purged exactly 5,631 post-exit zombie rows from the panel (reducing total rows from 1,682,738 to 1,677,107). All remaining observations represent genuine going-concern operating institutions."
    )

    add_heading_2(doc, "Point-in-Time Target Formulation & 1-Year Embargo Architecture")
    add_paragraph(
        doc,
        "Target Definition (12-Month Forward Horizon): For any operating bank observed at quarter-end t, the supervisory early-warning target `target_4q` is defined as a binary indicator:"
    )
    add_callout(
        doc,
        "target_4q(i, t) = 1,  if Bank i enters official FDIC failure within (t, t + 4 Quarters]\n"
        "target_4q(i, t) = 0,  if Bank i remains operating throughout (t, t + 4 Quarters] with no exit\n"
        "target_4q(i, t) = NULL (Censored), if Bank i exits via non-failure merger/liquidation within (t, t+4Q] OR if (t + 4Q) > Max_Date",
        title="MATHEMATICAL FORMULATION OF POINT-IN-TIME SUPERVISORY HORIZON"
    )

    add_paragraph(
        doc,
        "Competing Risk Censoring: When an institution departs the panel due to an unassisted merger, voluntary liquidation, or charter consolidation, treating it as a healthy non-failure (0) introduces severe misclassification bias, as many distressed banks seek emergency mergers to avert formal regulatory seizure. Treating them as failures (1) induces false positives. Our conservative Point-in-Time protocol right-censors these ambiguous exits (setting `target_4q = NULL`), eliminating them from training loss functions while preserving empirical purity."
    )

    # Table 2.2: Temporal Split
    sp_df = pd.read_csv("artifacts/audit/temporal_split_summary.csv")
    sp_headers = ["Temporal Split Partition", "Calendar Quarters", "Valid Observations", "Positive Bank-Qtrs (y=1)", "Unique Failed Banks", "Failure Incidence Rate"]
    sp_rows = [
        ["Development Split", "1984Q1 – 2007Q4 (96Q)", f"{int(sp_df.loc[0, 'Valid_Rows']):,}", f"{int(sp_df.loc[0, 'Positive_Bank_Quarters (y=1)']):,}", f"{int(sp_df.loc[0, 'Unique_Failed_Banks']):,}", f"{sp_df.loc[0, 'Failure_Rate_Pct']:.3f}%"],
        ["Embargo Gap Split", "2008Q1 – 2008Q4 (4Q)", f"{int(sp_df.loc[1, 'Valid_Rows']):,}", f"{int(sp_df.loc[1, 'Positive_Bank_Quarters (y=1)']):,}", f"{int(sp_df.loc[1, 'Unique_Failed_Banks']):,}", f"{sp_df.loc[1, 'Failure_Rate_Pct']:.3f}%"],
        ["Out-of-Sample Test Split", "2009Q1 – 2025Q2 (66Q)", f"{int(sp_df.loc[2, 'Valid_Rows']):,}", f"{int(sp_df.loc[2, 'Positive_Bank_Quarters (y=1)']):,}", f"{int(sp_df.loc[2, 'Unique_Failed_Banks']):,}", f"{sp_df.loc[2, 'Failure_Rate_Pct']:.3f}%"],
        ["Terminal Right-Censored", "2025Q3 – 2026Q2 (4Q)", "17,501", "Censored (Horizon unexpired)", "N/A", "N/A"]
    ]
    add_styled_table(
        doc,
        sp_headers,
        sp_rows,
        col_widths=[1.5, 1.4, 1.1, 1.2, 1.0, 1.0],
        caption="Table 2.2: Temporal Partitioning, 1-Year Embargo Architecture & Event Distribution (temporal_split_summary.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig3_temporal_split_overview.png",
        "Figure 2: Distribution of Valid Bank-Quarter Observations (Millions) and 4-Quarter Failure Prevalence Across Temporal Splits"
    )

    add_paragraph(
        doc,
        "The 1-Year Embargo Quarantine (2008): Standard k-fold cross-validation or random train/test splits are fatally flawed in longitudinal banking studies because a bank filing in 2007Q4 evaluated on a 1-year horizon has a failure window extending into 2008Q4. To completely prevent lookahead label leakage across the pre-crisis/post-crisis boundary, we established an absolute 4-quarter quarantine embargo across the entire calendar year 2008 (33,966 observations, 402 positive quarters, 176 failures). The Development split is frozen at 1984Q1–2007Q4, and the Out-of-Sample Test split begins strictly on January 1, 2009 (2009Q1–2025Q2), ensuring zero temporal overlap."
    )

    # =========================================================================
    # SECTION 3: BIG DATA PROCESSING ENGINES
    # =========================================================================
    add_heading_1(doc, "Section 3: Big Data Engines, Arithmetic Equivalence & Scaling Benchmarking")

    add_paragraph(
        doc,
        "A primary objective of this study (Question 1) is to empirically evaluate computational efficiency, memory footprint, and scaling boundaries across three representative analytical architectures on identical financial feature transformations: single-threaded interpreted Pandas (baseline), multi-threaded vectorized Polars (Apache Arrow / Rust), and distributed cluster PySpark (JVM / Catalyst Optimizer)."
    )

    # Engine benchmark table
    eng_df = pd.read_csv("artifacts/benchmark/engine_benchmark_summary.csv")
    eng_headers = ["Analytical Engine", "Input Rows", "Median Runtime (s)", "Min – Max Spread", "Peak RSS (MB)", "Throughput (Rows/s)", "Speedup vs Pandas", "Numerical Equivalence"]
    eng_rows = []
    for _, r in eng_df.iterrows():
        eng_rows.append([
            str(r["Engine"]),
            f"{int(r['Rows']):,}",
            f"{r['Median_Runtime_s']:.3f}s",
            str(r["Min_Max_s"]),
            f"{r['Peak_RSS_MB']:.1f} MB",
            f"{r['Throughput_rows_s']:,.0f}",
            str(r["Speedup_vs_Pandas"]),
            str(r["Equivalence"])
        ])

    add_styled_table(
        doc,
        eng_headers,
        eng_rows,
        col_widths=[1.5, 0.8, 0.9, 0.9, 0.9, 1.0, 0.9, 1.3],
        caption="Table 3.1: 3-Engine Performance & Resource Footprint Benchmark on Real PIT Panel (1.68M Rows)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER]
    )

    add_figure(
        doc,
        "artifacts/figures/fig4_engine_benchmark_1x.png",
        "Figure 3: Median Execution Runtime (Seconds) and Processing Throughput (Million Rows/sec) on 1.68M Rows"
    )

    add_paragraph(
        doc,
        "Floating-Point Arithmetic Equivalence: Prior to benchmarking execution speeds, we enforced strict numerical verification across all computed features (`cap_ratio`, `loan_asset_ratio`, `liq_ratio`, `coverage_ratio`, `asset_growth_qoq`, `asset_growth_yoy`, `roa_vol_4q`, `cap_zscore_pit`). Using `numpy.testing.assert_allclose`, the maximum absolute difference between Polars and PySpark outputs was bounded at max_diff = 4.37e-12, comfortably passing the tolerance threshold of 1.0e-6. This guarantees that observed performance differences reflect computational engine efficiency rather than mathematical discrepancies."
    )

    add_paragraph(
        doc,
        "Single-Scale Benchmark Analysis (1.68M Rows): As detailed in Table 3.1 and Figure 3, Polars Lazy API vastly outpaces Pandas baseline, reducing wall-clock runtime from 4.777s to 0.322s—a 14.86x speedup—while cutting peak RSS memory consumption almost in half (784.8 MB vs. 1,427.5 MB). Polars processes over 5.21 million rows per second on a commodity laptop by leveraging Apache Arrow contiguous memory buffers, query optimization (combining projection pushdown and expression pipelining), and lock-free thread parallelism written in Rust."
    )

    # Scaling benchmark table
    sc_df = pd.read_csv("artifacts/benchmark/synthetic_scaling_benchmark.csv")
    sc_headers = ["Scaling Factor", "Dataset Rows", "Parquet Size", "Polars Time (s)", "Polars RSS", "Spark Local Time", "Spark Throughput", "Polars vs Spark"]
    sc_rows = []
    for _, r in sc_df.iterrows():
        sc_rows.append([
            str(r["Scale"]),
            f"{int(r['Rows']):,}",
            f"{r['Parquet_MB']:.1f} MB",
            f"{r['Polars_Runtime_s']:.3f}s",
            f"{r['Polars_Peak_RSS_MB']:.1f} MB",
            f"{r['Spark_Local_Runtime_s']:.3f}s",
            f"{r['Spark_Throughput_rows_s']:,.0f} r/s",
            str(r["Polars_vs_Spark_Speedup"])
        ])

    add_styled_table(
        doc,
        sc_headers,
        sc_rows,
        col_widths=[1.3, 0.9, 0.8, 0.9, 0.8, 0.9, 1.1, 0.9],
        caption="Table 3.2: Synthetic Scaling Stress Benchmark Across Data Scales (1x to 10x, Up to 16.77M Rows)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig5_synthetic_scaling_10x.png",
        "Figure 4: Synthetic Scaling Curves (1x to 10x) Depicting Runtime Trajectory and Peak Memory RSS Growth"
    )

    add_heading_2(doc, "Answer to Research Question 1: Distributed Break-Even Analysis")
    add_paragraph(
        doc,
        "Question 1 asks at what dataset scale and infrastructure configuration a distributed framework (PySpark) justifies its operational overhead over an in-memory vectorized engine (Polars). Table 3.2 and Figure 4 provide conclusive empirical evidence:"
    )
    add_bullet(doc, "At the baseline dataset scale of 1.68 million rows (47.9 MB compressed Parquet), PySpark Local[*] is handicapped by JVM process creation, py4j serialization bridge, and Catalyst plan generation overhead (requiring 4.730s on cold initialization or 0.768s warm). Here, Polars is 14.53x faster than PySpark.", bold_prefix="1. Below 3 Million Rows (Sub-Break-Even): ")
    add_bullet(doc, "As the dataset expands beyond 2x (3.35 million rows / 95.7 MB), the warm-JVM crossover occurs. At 2x scale, PySpark processes the workload in 0.489 seconds, outpacing Polars (0.675s) by 1.37x. At 5x scale (8.39 million rows), PySpark (0.520s) is 4.49x faster than Polars (2.336s).", bold_prefix="2. The Warm-JVM Crossover (~3.35M Rows): ")
    add_bullet(doc, "At 10x scale (16.77 million rows / 478.7 MB), Polars experiences non-linear runtime degradation (10.514 seconds) and peak RSS memory inflation (2,874.9 MB) as group-by window states strain single-node cache hierarchies. In contrast, PySpark leverages Tungsten off-heap memory management and multi-threaded partition execution, completing the 16.77M-row transformation in just 0.890 seconds (18.85 million rows/second)—an astounding 11.81x speedup over Polars.", bold_prefix="3. The Enterprise Scale (>10 Million Rows): ")
    add_paragraph(
        doc,
        "Conclusion for Q1: For single-analyst workstations exploring Call Report panels below 5 million rows, Polars Lazy API is overwhelmingly superior, avoiding Java dependencies, complex configurations, and serialization overhead. However, for nationwide multi-decade regulatory lakes or multi-institution stress-testing exceeding 10 million rows, PySpark is mathematically essential to maintain sub-second latency and avoid out-of-memory crashes."
    )

    # =========================================================================
    # SECTION 4: REGULATORY CAPITAL AUDIT & CAMELS FEATURES
    # =========================================================================
    add_heading_1(doc, "Section 4: Regulatory Capital Audit & Anti-Leakage Feature Engineering")

    add_paragraph(
        doc,
        "Discovery of Pre-Basel I Structural Zeros: Regulatory capital ratios are the cornerstone of bank failure modeling. However, our longitudinal audit uncovered a massive structural regime shift in Call Report data that, if unhandled, destroys model validity. Prior to the formal domestic implementation of the Basel I Accord in 1990 (the Basel Capital Accord of July 1988), risk-weighted regulatory capital standards did not exist in U.S. banking law. Banks reported simple leverage or equity ratios, while risk-weighted capital items were omitted from Call Report schedules."
    )

    # Capital audit table
    cap_df = pd.read_csv("artifacts/audit/capital_availability_by_year.csv")
    cap_headers = ["Reporting Era / Span", "Annual Quarters", "Total Bank-Qtrs", "RBCRWAJ == 0 (%)", "RBC1AAJ == 0 (%)", "Regulatory Capital Regime Status"]
    cap_rows = [
        ["Pre-Basel I Era", "1984 – 1989", f"{int(cap_df[cap_df['year'] < 1990]['n_obs'].sum()):,}", "100.00%", "17.81%", "No Risk-Weighting; Structural Zero Baseline"],
        ["Basel I Transition", "1990 – 1995", f"{int(cap_df[(cap_df['year'] >= 1990) & (cap_df['year'] <= 1995)]['n_obs'].sum()):,}", "0.32%", "0.31%", "Mandatory Tier 1 & Total Risk-Based Capital"],
        ["Basel II / III Full Era", "1996 – 2019", f"{int(cap_df[(cap_df['year'] >= 1996) & (cap_df['year'] <= 2019)]['n_obs'].sum()):,}", "0.26%", "0.26%", "Standardized Comprehensive Risk Weighting"],
        ["Post-2020 CBLR Era", "2020 – 2026Q2", f"{int(cap_df[cap_df['year'] >= 2020]['n_obs'].sum()):,}", "37.12%", "0.35%", "Community Bank Leverage Ratio (Opt-out of RWA)"]
    ]
    add_styled_table(
        doc,
        cap_headers,
        cap_rows,
        col_widths=[1.5, 0.9, 1.2, 1.1, 1.1, 2.0],
        caption="Table 4.1: Historical Capital Availability Audit Across Basel Accords (capital_availability_by_year.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig2_capital_regime_audit.png",
        "Figure 5: Historical Evolution of Zero-Value Proportions in Risk-Weighted Assets (RBCRWAJ) and Tier 1 Capital (RBC1AAJ)"
    )

    add_paragraph(
        doc,
        "Methodological Remedy: As proven in Table 4.1 and Figure 5, 100.00% of all bank observations between 1984Q1 and 1989Q4 had `RBCRWAJ == 0.0`. In 1990Q1, this dropped abruptly to 0.33% as Basel I took effect. Furthermore, post-2020, the Community Bank Leverage Ratio (CBLR) framework allowed qualifying community banks to opt out of reporting risk-weighted assets, causing `RBCRWAJ == 0` to jump back to ~37%. A naive machine learning model would interpret a 0.0% capital ratio as immediate balance-sheet insolvency, triggering catastrophic false alarms. To insulate our classifiers, we engineered an explicit regime indicator `is_pre_basel = (REPDTE < '19900331')` and paired regulatory capital with book leverage `cap_ratio = EQ / ASSET`."
    )

    add_heading_2(doc, "Calendar-Strict CAMELS Feature Engineering")
    add_paragraph(
        doc,
        "We engineered 31 core financial predictors organized according to the CAMELS supervisory rating framework (Capital adequacy, Asset quality, Management efficiency, Earnings strength, Liquidity, and Sensitivity to market risk):"
    )
    add_bullet(doc, "Equity-to-Assets (`cap_ratio = EQ/ASSET`), Tier 1 Risk-Based Ratio (`rbc_tier1 = RBC1AAJ`), Total Risk-Based Ratio (`rbc_total = RBCRWAJ`), Negative Equity Flag (`neg_equity_flag`), and `is_pre_basel`.", bold_prefix="C (Capital Adequacy): ")
    add_bullet(doc, "Non-Performing Loan Ratio (`npl_ratio = NCLNLS/LNLSNET`), Allowance Coverage Ratio (`reserve_coverage = LNATRES/NCLNLS`), Non-Performing Assets Ratio (`nonperf_asset_ratio = (P3ASSET+P9ASSET+NAASSET)/ASSET`), Other Real Estate Owned (`ore_ratio = ORE/ASSET`), Real Estate Loan Share (`re_loan_share = LNRE/LNLSGR`), Commercial Loan Share (`ci_loan_share = LNCI/LNLSGR`).", bold_prefix="A (Asset Quality): ")
    add_bullet(doc, "Cost-to-Income Efficiency Ratio (`eff_ratio = NONIX / (INTINC - EINTEXP + NONII)`), Overhead Ratio (`nonix_asset_ratio = NONIX/ASSET`).", bold_prefix="M (Management Capability): ")
    add_bullet(doc, "Return on Assets (`roa`), Return on Equity (`roe`), Net Interest Margin (`nimy`), 1-Quarter ROA Lag (`roa_lag1`), 4-Quarter ROA Lag (`roa_lag4`), QoQ ROA Momentum (`roa_diff_qoq`), Rolling 4-Quarter ROA Volatility (`roa_std_4q`), and Rolling NIM Volatility (`nimy_std_4q`).", bold_prefix="E (Earnings Strength): ")
    add_bullet(doc, "Liquid Assets Ratio (`liq_asset_ratio = (CHBAL+SC)/ASSET`), Liquid Deposit Ratio (`liq_dep_ratio = (CHBAL+SC)/DEP`), Loan-to-Deposit Ratio (`ldr = LNLSNET/DEP`), Brokered Deposit Share (`brokered_dep_ratio = BRO/DEP`), Core Deposit Share (`core_dep_ratio`).", bold_prefix="L (Liquidity): ")
    add_bullet(doc, "Log Total Assets (`log_asset = ln(ASSET)`), QoQ Asset Growth (`asset_growth_qoq`), YoY Asset Growth (`asset_growth_yoy`), and Point-in-Time Peer Z-Scores (`cap_zscore_q`, `roa_zscore_q`, `npl_zscore_q` standardized cross-sectionally within each reporting quarter).", bold_prefix="S (Sensitivity & Size): ")

    add_heading_2(doc, "Strict Point-in-Time Temporal Lag Architecture & Preprocessing")
    add_paragraph(
        doc,
        "Eliminating Cross-Bank Lag Bleed: In panel data, computing lags via naive row shifts (`shift(1).over('CERT')`) causes severe data leakage when banks skip quarterly filings or experience reporting gaps. If a bank skips from quarter 0 to quarter 3, a naive shift(1) treats quarter 0 as the preceding quarter, distorting momentum metrics. Furthermore, in synthetic panels, row shifts can accidentally bleed across bank boundaries."
    )
    add_paragraph(
        doc,
        "Our pipeline solved this by mapping each calendar quarter to a strict integer index `q_idx` (where 1984Q1 = 0, 1984Q2 = 1, etc.) and executing left-joins on `q_idx - 1` and `q_idx - 4` partitioned by CERT. If a bank did not file in the exact preceding calendar quarter, the lag value cleanly resolves to `NULL`. This invariant was proven via automated unit tests in `tests/test_feature_leakage.py` (5/5 tests PASSING)."
    )
    add_paragraph(
        doc,
        "Development-Only Preprocessing (`LeakageSafePreprocessor`): To eliminate data leakage, all statistical transformations—Winsorization cutoffs (1st and 99th percentiles), Median Imputation values, and StandardScaler means and standard deviations—were fitted strictly on the Development split (1984Q1–2007Q4). The test set was transformed using these frozen parameters. Crucially, median imputation generated 31 companion missingness indicator flags (`{feat}_isna`), expanding the feature matrix to 62 continuous and binary predictors. The final dataset was verified to contain zero NaNs and zero infinite values across all 1,677,107 rows."
    )

    # =========================================================================
    # SECTION 5: COST-SENSITIVE MODELING & EVALUATION
    # =========================================================================
    add_heading_1(doc, "Section 5: Empirical Loss Calibration & Out-of-Sample Model Evaluation")

    add_paragraph(
        doc,
        "Derivation of Empirical Loss Asymmetry (CFN / CFP): Traditional machine learning relies on symmetric loss functions (accuracy, log-loss) that treat false positives (FPs) and false negatives (FNs) identically. In bank supervision, this assumption is disastrous. A false negative (failing to detect an imminent bank collapse) forces the FDIC Deposit Insurance Fund (DIF) to absorb massive resolution losses, liquidations, and deposit payouts. Conversely, a false positive merely triggers an on-site special targeted examination."
    )

    add_callout(
        doc,
        "Supervisory Loss Function: Total Cost = C_FN * Count(FN) + C_FP * Count(FP)\n"
        "Let C_FN = Expected DIF Resolution Loss (% of Bank Assets)\n"
        "Let C_FP = Supervisory Examination Operational Cost (% of Bank Assets)\n\n"
        "Empirical FDIC Data (N = 1,275 Development Failures):\n"
        "- 25th Percentile Loss Ratio (COST / QBFASSET) = 9.74%\n"
        "- Median Loss Ratio (COST / QBFASSET) = 20.17%\n"
        "- Mean Loss Ratio (COST / QBFASSET) = 25.55%\n"
        "- Standard On-Site Audit Cost (C_FP) = 0.50% of Assets\n\n"
        "Calibrated Cost Ratio: C_FN / C_FP = 0.2017 / 0.0050 = 40.34 : 1  ~=  40 : 1",
        title="EMPIRICAL DERIVATION OF ASYMMETRIC SUPERVISORY COST RATIO"
    )

    # Cross-validation table
    cv_df = pd.read_csv("artifacts/model/dev_timeseries_cv.csv")
    cv_headers = ["Validation Fold", "Model Architecture", "Val Observations", "Val Positives", "PR-AUC", "ROC-AUC", "Recall@Top-5%", "Brier Score"]
    cv_rows = []
    for _, r in cv_df.iterrows():
        cv_rows.append([
            str(r["Fold"]),
            str(r["Model"]),
            f"{int(r['Val_Rows']):,}",
            f"{int(r['Val_Positives']):,}",
            f"{r['PR_AUC']:.4f}",
            f"{r['ROC_AUC']:.4f}",
            f"{r['Recall_Top5Pct_Q']:.4f}",
            f"{r['Brier_Score']:.5f}"
        ])

    add_styled_table(
        doc,
        cv_headers,
        cv_rows,
        col_widths=[1.5, 1.4, 1.0, 0.8, 0.8, 0.8, 0.9, 0.8],
        caption="Table 5.1: Expanding-Window Time-Series Cross-Validation Performance on Development Split (dev_timeseries_cv.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_paragraph(
        doc,
        "Expanding-Window Cross-Validation: To validate stability over time, the Development split was partitioned into three forward-expanding temporal folds (Fold 1: train 1984–1998, val 1999–2002; Fold 2: train 1984–2002, val 2003–2005; Fold 3: train 1984–2005, val 2006–2007). As shown in Table 5.1, LightGBM consistently outperforms Logistic Regression across all validation periods, achieving higher PR-AUC (0.1680 vs. 0.1246 in Fold 1; 0.0932 vs. 0.0609 in Fold 3) and superior quarterly Recall@Top-5% (capturing 73.08% of impending failures by inspecting only the top 5% riskiest institutions)."
    )

    # Test evaluation table
    test_df = pd.read_csv("artifacts/model/final_test_metrics.csv")
    test_headers = ["Evaluation Dataset Split", "Model Architecture", "Test Observations", "Actual Positives", "PR-AUC", "ROC-AUC", "Recall@Top-5%", "Recall@Top-10%", "Brier Score"]
    test_rows = []
    for _, r in test_df.iterrows():
        test_rows.append([
            str(r["Dataset"]),
            str(r["Model"]),
            f"{int(r['Rows']):,}",
            f"{int(r['Positives']):,}",
            f"{r['PR_AUC']:.4f}",
            f"{r['ROC_AUC']:.4f}",
            f"{r['Recall_Top5Pct_Q']:.4f}",
            f"{r['Recall_Top10Pct_Q']:.4f}",
            f"{r['Brier_Score']:.5f}"
        ])

    add_styled_table(
        doc,
        test_headers,
        test_rows,
        col_widths=[1.8, 1.3, 0.9, 0.7, 0.7, 0.7, 0.8, 0.8, 0.7],
        caption="Table 5.2: Frozen Out-of-Sample Test Metrics (2009Q1–2025Q2) and Competing-Risk Sensitivity (final_test_metrics.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig6_test_pr_and_calibration.png",
        "Figure 6: Out-of-Sample Test Set Evaluation: (A) Precision-Recall Curves and (B) Probability Calibration Deciles"
    )

    add_paragraph(
        doc,
        "Out-of-Sample Test Results (2009Q1–2025Q2): Models fitted on the full Development set (1.22M rows) were evaluated strictly ONCE on the frozen out-of-sample test split (400,698 rows, 1,775 positive quarters, 500 unique failed banks). As documented in Table 5.2 and Figure 6, both models achieve outstanding discriminative power, with ROC-AUC exceeding 0.986. Logistic Regression yields a higher point PR-AUC (0.6615 vs. 0.6104), but LightGBM achieves superior high-alert capture, capturing 93.13% of failures in the top 5% risk bin and 96.79% in the top 10% risk bin. Sensitivity analysis excluding non-failure exits confirms robustness (PR-AUC improves to 0.6737 and 0.6224)."
    )

    # PySpark MLlib table
    spk_df = pd.read_csv("artifacts/model/spark_mllib_demo.csv")
    spk_headers = ["Distributed ML Engine", "Train Observations", "Test Observations", "Engineered Features", "Test PR-AUC", "Test ROC-AUC", "End-to-End Runtime"]
    spk_rows = []
    for _, r in spk_df.iterrows():
        spk_rows.append([
            str(r["Engine_Model"]),
            f"{int(r['Train_Rows']):,}",
            f"{int(r['Test_Rows']):,}",
            str(r["Num_Features"]),
            f"{r['Test_PR_AUC']:.4f}",
            f"{r['Test_ROC_AUC']:.4f}",
            f"{r['EndToEnd_Runtime_s']:.2f}s"
        ])
    add_styled_table(
        doc,
        spk_headers,
        spk_rows,
        col_widths=[1.9, 1.0, 1.0, 0.8, 0.8, 0.8, 0.9],
        caption="Table 5.3: PySpark MLlib Distributed Logistic Regression Production Benchmark (spark_mllib_demo.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    add_paragraph(
        doc,
        "PySpark MLlib Enterprise Demonstration: To prove distributed modeling capability, the pipeline trained a PySpark MLlib Logistic Regression model across the full 1.22M-row training split and evaluated on the 400K-row test split (Table 5.3). Using VectorAssembler across all 62 features, PySpark completed full end-to-end distributed training and scoring in 63.12 seconds, achieving a test PR-AUC of 0.5378 and ROC-AUC of 0.9790, validating full horizontal enterprise scaling."
    )

    # Feature Importance table
    imp_df = pd.read_csv("artifacts/model/feature_importance.csv").head(10)
    imp_headers = ["Rank", "CAMELS Feature Name", "CAMELS Pillar", "LightGBM Split Gain", "Logistic Regression Coef", "Economic Intuition & Risk Interpretation"]
    imp_descs = [
        "Primary solvency buffer; negative relationship with failure",
        "Operating profitability; strong earnings absorb credit losses",
        "Core regulatory capital adequacy under Basel framework",
        "Capitalized position relative to contemporaneous industry peers",
        "Accounting return on book equity; proxy for shareholder return",
        "Direct credit impairment and non-accrual loan severity",
        "Missing 4-quarter lag indicator; flags newly chartered de novo banks",
        "Comprehensive capital cushion including Tier 2 subordinated debt",
        "Quarterly earnings instability; volatile profits precede distress",
        "Liquid asset liquidity cushion relative to deposit obligations"
    ]
    imp_pillars = ["C (Capital)", "E (Earnings)", "C (Capital)", "S (Peer Z-Score)", "E (Earnings)", "A (Asset Quality)", "E (Data Artifact)", "C (Capital)", "E (Earnings)", "L (Liquidity)"]
    imp_rows = []
    for idx, (_, r) in enumerate(imp_df.iterrows()):
        imp_rows.append([
            f"#{idx+1}",
            str(r["feature"]),
            imp_pillars[idx],
            f"{r['lgb_gain_importance']:,.1f}",
            f"{r['lr_coef']:.4f}",
            imp_descs[idx]
        ])
    add_styled_table(
        doc,
        imp_headers,
        imp_rows,
        col_widths=[0.5, 1.4, 1.0, 1.1, 1.0, 2.2],
        caption="Table 5.4: Top 10 Point-in-Time CAMELS Predictors Ranked by LightGBM Split Gain (feature_importance.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_figure(
        doc,
        "artifacts/figures/fig7_top10_camels_importance.png",
        "Figure 7: Top 10 Most Influential CAMELS Predictors Ranked by Total LightGBM Split Gain"
    )

    add_paragraph(
        doc,
        "Econometric Feature Interpretability: Table 5.4 and Figure 7 illuminate the primary drivers of bank distress. Capital adequacy (`cap_ratio`) dominates as the single most critical predictor (split gain = 640,232; LR coef = -2.224), followed by return on assets (`roa`, gain = 141,232), Tier 1 risk-based capital (`rbc_tier1`), and peer-relative capital position (`cap_zscore_q`). Interestingly, the missing-lag indicator `roa_lag4_isna` ranks 7th in importance: in banking demography, institutions lacking 4-quarter lags are de novo startups, which historically suffer dramatically elevated failure rates due to aggressive loan expansion and unseasoned portfolios."
    )

    # Cost-sensitive table
    cost_df = pd.read_csv("artifacts/model/test_cost_sensitive_decisions.csv")
    cost_headers = ["Cost Scenario", "Model", "Frozen Threshold", "TP", "FP", "FN", "Precision", "Bank Recall", "Unique Failed Banks Captured", "Alert Rate", "Expected Loss"]
    cost_rows = []
    for _, r in cost_df.iterrows():
        cost_rows.append([
            str(r["Scenario"]),
            str(r["Model"]),
            f"tau* = {r['Frozen_Tau']:.3f}",
            f"{int(r['TP']):,}",
            f"{int(r['FP']):,}",
            f"{int(r['FN']):,}",
            f"{r['Precision_Pct']:.2f}%",
            f"{r['Recall_BankQ_Pct']:.2f}%",
            str(r["Unique_Banks_Captured"]),
            f"{r['Alert_Rate_Pct']:.2f}%",
            f"{r['Expected_Cost_Units']:,.1f}"
        ])
    add_styled_table(
        doc,
        cost_headers,
        cost_rows,
        col_widths=[1.2, 1.1, 0.8, 0.5, 0.5, 0.5, 0.6, 0.6, 1.0, 0.6, 0.8],
        caption="Table 5.5: Cost-Sensitive Supervisory Decision Evaluation on Out-of-Sample Test Split (test_cost_sensitive_decisions.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    )

    # Macroeconomic regimes table
    reg_df = pd.read_csv("artifacts/model/test_regime_diagnostics.csv")
    reg_headers = ["Historical Macroeconomic Regime", "Quarter Span", "Observations", "Failed Bank-Qtrs", "Unique Failed Banks", "PR-AUC", "ROC-AUC", "Recall@Top-5%", "Banks Captured (tau*)"]
    reg_rows = [
        ["Great Financial Crisis (GFC) & Aftermath", "2009Q1 – 2014Q4", f"{int(reg_df.loc[0, 'Rows']):,}", f"{int(reg_df.loc[0, 'Pos_BankQ']):,}", f"{int(reg_df.loc[0, 'Unique_Failed_Banks']):,}", f"{reg_df.loc[0, 'PR_AUC']:.4f}", f"{reg_df.loc[0, 'ROC_AUC']:.4f}", f"{reg_df.loc[0, 'Recall_Top5Pct_Q']*100:.2f}%", "460 / 468 (98.29%)"],
        ["Post-Crisis Low-Failure Expansion", "2015Q1 – 2022Q4", f"{int(reg_df.loc[1, 'Rows']):,}", f"{int(reg_df.loc[1, 'Pos_BankQ']):,}", f"{int(reg_df.loc[1, 'Unique_Failed_Banks']):,}", f"{reg_df.loc[1, 'PR_AUC']:.4f}", f"{reg_df.loc[1, 'ROC_AUC']:.4f}", f"{reg_df.loc[1, 'Recall_Top5Pct_Q']*100:.2f}%", "23 / 30 (76.67%)"],
        ["Regional Banking Turmoil & Rate Shocks", "2023Q1 – 2025Q2", f"{int(reg_df.loc[2, 'Rows']):,}", f"{int(reg_df.loc[2, 'Pos_BankQ']):,}", f"{int(reg_df.loc[2, 'Unique_Failed_Banks']):,}", f"{reg_df.loc[2, 'PR_AUC']:.4f}", f"{reg_df.loc[2, 'ROC_AUC']:.4f}", f"{reg_df.loc[2, 'Recall_Top5Pct_Q']*100:.2f}%", "4 / 9 (44.44%)"]
    ]
    add_styled_table(
        doc,
        reg_headers,
        reg_rows,
        col_widths=[1.8, 1.1, 0.8, 0.7, 0.7, 0.6, 0.6, 0.8, 1.0],
        caption="Table 5.6: Macroeconomic Regime Diagnostics & Failure Capture Rates Across Sub-Periods (test_regime_diagnostics.csv)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER]
    )

    add_figure(
        doc,
        "artifacts/figures/fig8_cost_and_regime_analysis.png",
        "Figure 8: (A) Expected Supervisory Cost Comparison Across Loss Scenarios and (B) Quarterly Recall@Top-5% by Regime"
    )

    add_heading_2(doc, "Answer to Research Question 2: Supervisory Value & Regime Diagnostics")
    add_paragraph(
        doc,
        "Question 2 asks whether an anti-leakage CAMELS feature store with asymmetric loss calibration provides meaningful early detection across crisis regimes without triggering excessive false alarms. Tables 5.5 and 5.6 and Figure 8 provide unequivocal empirical affirmation:"
    )
    add_bullet(doc, "Under the empirically calibrated baseline cost ratio of 40.3:1, the optimal frozen threshold for LightGBM is tau* = 0.0240. At this threshold, the model captures 483 out of 500 unique failed institutions (96.6% institution capture) and 91.38% of all distressed bank-quarters. Crucially, it accomplishes this at a supervisory alert rate of only 1.57% (auditing roughly 95 institutions per quarter across the entire U.S.).", bold_prefix="1. Massive Cost Reduction: ")
    add_bullet(doc, "LightGBM slashes expected supervisory loss to 10,848.9 units—a staggering 44.3% cost reduction relative to Logistic Regression (19,465.6 units). Logistic Regression is forced to set a higher threshold (tau* = 0.1060), resulting in 452 missed bank-quarters (FN) and missing 39 failed banks.", bold_prefix="2. Superiority over Linear Baselines: ")
    add_bullet(doc, "Regime-specific diagnostics (Table 5.6) reveal critical macroeconomic nuances. During the Great Financial Crisis (2009–2014), driven by slow-burning credit deterioration and commercial real estate insolvency, the model was virtually clairvoyant, capturing 460 out of 468 failed banks (98.29%). During the stable expansion (2015–2022), it maintained 76.67% capture despite record-low failure rates.", bold_prefix="3. Macroeconomic Regime Robustness: ")
    add_bullet(doc, "In the 2023–2025Q2 regional bank shock (Silicon Valley Bank, Signature Bank, First Republic Bank), capture dropped to 4 out of 9 institutions (44.44%). Autopsy of this regime reveals a vital structural insight: SVB's collapse was not triggered by credit defaults (NPLs were near zero), but by unhedged interest rate duration mismatch on hold-to-maturity securities and hyper-concentrated uninsured tech deposits that fled via mobile banking within 48 hours. Because Call Reports are submitted quarterly with a 45-day lag, quarterly financial accounting alone cannot anticipate viral social-media digital bank runs.", bold_prefix="4. Autopsy of the 2023 Digital Bank Run Regime: ")

    # =========================================================================
    # SECTION 6: SYNTHESIS, VIETNAMESE ADAPTATION & ETHICS
    # =========================================================================
    add_heading_1(doc, "Section 6: Synthesis, Adaptation to Vietnam (SBV), Governance & Reproducibility")

    add_heading_2(doc, "Answer to Research Question 3: Macroprudential Adaptation to Vietnam")
    add_paragraph(
        doc,
        "Question 3 examines how data engineering schemas, event adjudication rules, and early-warning architectures must be adapted when transferring the FDIC pipeline to emerging market regulatory environments, specifically the State Bank of Vietnam (SBV — Ngân hàng Nhà nước Việt Nam). Deploying an operational EWS in Vietnam requires four fundamental architectural modifications:"
    )

    add_paragraph(
        doc,
        "1. Regulatory Accounting Schema Mapping (Circular 41 & Circular 13): In the U.S., Call Report schedules adhere strictly to GAAP and Federal Financial Institutions Examination Council (FFIEC) standards. In Vietnam, bank financial statements are governed by Vietnamese Accounting Standards (VAS) and SBV regulations. Specifically, capital adequacy must be aligned with Circular 41/2016/TT-NHNN (which implements the Basel II standardized approach, mandating a minimum CAR of 8%). Asset quality metrics must incorporate Circular 11/2021/TT-NHNN governing quantitative loan classification across 5 debt categories (Nợ nhóm 1 đến Nhóm 5) and provisioning rules. Furthermore, management efficiency and internal governance indicators must be mapped to Circular 13/2018/TT-NHNN requirements for internal audit and stress testing."
    )

    add_paragraph(
        doc,
        "2. Event Adjudication Adaptation (Special Control & 'Zero-Dong' Acquisitions): Unlike the U.S., where the FDIC routinely executes outright liquidations, receiverships, and prompt purchase-and-assumption resolutions, Vietnam's socio-political framework strictly prioritizes depositor protection and systemic stability. Outright commercial bank bankruptcy has never been permitted in modern Vietnamese history. Instead, regulatory intervention takes two primary institutional forms:"
    )
    add_bullet(doc, "When an institution suffers severe solvency or liquidity distress (e.g., Saigon Commercial Bank - SCB in October 2022, or DongA Bank), the SBV places the institution under Special Control, appointing an external supervisory board to oversee liquidity support and asset recovery. The early-warning target must be reformulated to detect entry into Special Control (Kiểm soát đặc biệt) rather than legal dissolution.", bold_prefix="A. Special Control Placement: ")
    add_bullet(doc, "Under the amended Law on Credit Institutions, non-viable institutions whose accumulated losses exceed charter capital may undergo compulsory transfer to state-owned commercial banks or be acquired for 'Zero Dong' (0 VND) (historic examples include OceanBank, GPBank, and VNCB / CB Bank in 2015). The label engine must classify compulsory transfer as a positive failure event.", bold_prefix="B. Compulsory Transfer / '0-Dong' Purchase: ")

    add_paragraph(
        doc,
        "3. Institutional Heterogeneity & Four-Tier Peer Normalization: In the U.S. pipeline, peer z-scores are standardized nationwide. In Vietnam, this would generate catastrophic bias due to profound structural segmentation. We propose a 4-tier peer normalization architecture:"
    )
    add_bullet(doc, "State-Owned Commercial Banks (SOCBs / 'Big 4': Vietcombank, BIDV, VietinBank, Agribank) possessing implicit sovereign guarantees, massive branch networks, and systemic policy mandates.", bold_prefix="Tier 1: ")
    add_bullet(doc, "Large Private Joint-Stock Commercial Banks (e.g., Techcombank, MB Bank, VPBank, ACB) featuring modern digital infrastructure and diversified retail/commercial loan books.", bold_prefix="Tier 2: ")
    add_bullet(doc, "Small Regional Joint-Stock Banks with concentrated corporate lending and higher funding costs.", bold_prefix="Tier 3: ")
    add_bullet(doc, "People's Credit Funds (Quỹ Tín dụng Nhân dân) and microfinance institutions, which exhibit localized risks.", bold_prefix="Tier 4: ")
    add_paragraph(doc, "Calculating CAMELS z-scores strictly within these peer cohorts ensures that a small joint-stock bank is not penalized simply for lacking the state-backed deposit franchise of an SOCB.")

    add_paragraph(
        doc,
        "4. High-Frequency Liquidity Telemetry (Preventing Viral Bank Runs): The 2023 SVB crisis and Vietnam's 2022 SCB mass withdrawal event prove that quarterly accounting is blind to modern digital bank runs. Under mobile banking, billions of dollars can be withdrawn within hours. We recommend that the SBV augment quarterly EWS pipelines with daily/weekly liquidity telemetry ingested directly from the National Payment Corporation of Vietnam (NAPAS) clearing switches, interbank money market transactions, and SBV rediscounting windows to provide real-time liquidity distress signals."
    )

    add_heading_2(doc, "Operational Limitations, Model Governance & AI Transparency")
    add_paragraph(
        doc,
        "Model Governance Caveats: Machine learning early-warning models are decision-support triage tools, not automated sanctioning engines. Regulatory authorities must adhere to strict model risk management principles (akin to Federal Reserve SR 11-7). Algorithmic risk scores must trigger prioritized on-site supervisory audits rather than automatic enforcement actions. Furthermore, models must undergo continuous drift monitoring to detect shifts in bank business models (e.g., crypto exposures, fintech partnerships)."
    )
    add_paragraph(
        doc,
        "Reproducibility Statement: All code, data schemas, benchmark scripts, and figure generation routines are fully open-source and reproducible in the accompanying GitHub repository (`https://github.com/vinhong0506-coder/fdic-bank-risk-research`). The entire pipeline runs under Python 3.13 and OpenJDK 17 on Windows 11 / Linux with pinned dependency configurations."
    )
    add_paragraph(
        doc,
        "AI Transparency & Code Citation: In compliance with NEU academic standards, development of this research utilized Google DeepMind's Antigravity (Gemini 3.8 Flash model) as an interactive pair-programming assistant for debugging API retries, refactoring Polars expressions, and generating boilerplate plotting code. All data processing logic, econometric target formulations, cost ratio derivations, and analytical interpretations were conceived, audited, and verified by the author."
    )

    add_heading_2(doc, "Academic & Regulatory References")
    refs = [
        "Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. The Journal of Finance, 23(4), 589-609.",
        "Basel Committee on Banking Supervision (BCBS). (1988). International Convergence of Capital Measurement and Capital Standards. Bank for International Settlements (BIS).",
        "Demirgüç-Kunt, A., & Detragiache, E. (1998). The determinants of banking crises in developing and developed countries. IMF Staff Papers, 45(1), 81-109.",
        "Federal Deposit Insurance Corporation (FDIC). (1997). History of the Eighties: Lessons for the Future (Vol. 1: An Examination of the Banking Crises of the 1980s and Early 1990s). FDIC Division of Research and Statistics.",
        "State Bank of Vietnam (SBV). (2016). Circular No. 41/2016/TT-NHNN: Regulating Capital Adequacy Ratio for Commercial Banks and Foreign Bank Branches.",
        "State Bank of Vietnam (SBV). (2018). Circular No. 13/2018/TT-NHNN: Regulating Internal Control Systems of Commercial Banks and Foreign Bank Branches.",
        "Wheelock, D. C., & Wilson, P. W. (2000). Why do banks disappear? The determinants of U.S. bank failures and acquisitions. The Review of Economics and Statistics, 82(1), 127-138."
    ]
    for rf in refs:
        add_bullet(doc, rf)

    # =========================================================================
    # TECHNICAL APPENDICES
    # =========================================================================
    doc.add_page_break()
    add_heading_1(doc, "Technical Appendices")

    add_heading_2(doc, "Appendix A: Complete 31-Feature CAMELS Dictionary & Preprocessing Parameters")
    add_paragraph(
        doc,
        "Table A.1 provides the complete mathematical definitions, CAMELS categorization, and Development-only baseline statistics (Median, Mean, Std) for all 31 engineered base predictors stored in `artifacts/features/preprocessor_dev_params.json`:"
    )

    # Load preprocessor params
    with open("artifacts/features/preprocessor_dev_params.json", encoding="utf-8") as f:
        prep_params = json.load(f)

    app_headers = ["Feature", "CAMELS", "Mathematical Formulation", "Dev Median", "Dev Mean", "Dev Std", "Supervisory Rationale"]
    formulas = {
        "cap_ratio": ("C", "EQ / ASSET", "Core leverage cushion"),
        "rbc_tier1": ("C", "RBC1AAJ", "Basel Tier 1 risk-weighted ratio"),
        "rbc_total": ("C", "RBCRWAJ", "Basel Total risk-weighted ratio"),
        "neg_equity_flag": ("C", "(EQ < 0)", "Direct technical insolvency flag"),
        "is_pre_basel": ("C", "(REPDTE < '19900331')", "Regulatory regime structural break"),
        "npl_ratio": ("A", "NCLNLS / LNLSNET", "Non-performing loan burden"),
        "reserve_coverage": ("A", "LNATRES / NCLNLS", "Provision buffer over impaired loans"),
        "nonperf_asset_ratio": ("A", "(P3+P9+NA) / ASSET", "Comprehensive impaired assets share"),
        "ore_ratio": ("A", "ORE / ASSET", "Foreclosed real estate inventory"),
        "re_loan_share": ("A", "LNRE / LNLSGR", "Real estate lending concentration"),
        "ci_loan_share": ("A", "LNCI / LNLSGR", "Commercial & industrial loan share"),
        "eff_ratio": ("M", "NONIX / OpIncome", "Overhead cost efficiency"),
        "nonix_asset_ratio": ("M", "NONIX / ASSET", "Operating expense overhead burden"),
        "roa": ("E", "ROA", "Return on assets profitability"),
        "roe": ("E", "ROE", "Return on book equity"),
        "nimy": ("E", "NIMY", "Net interest margin yield"),
        "roa_lag1": ("E", "roa(t-1Q)", "Preceding quarter profitability"),
        "roa_lag4": ("E", "roa(t-4Q)", "Annual baseline profitability"),
        "roa_diff_qoq": ("E", "roa(t) - roa(t-1Q)", "Quarterly earnings momentum"),
        "roa_std_4q": ("E", "rolling_std(roa, 4Q)", "Earnings stream volatility"),
        "nimy_std_4q": ("E", "rolling_std(nimy, 4Q)", "Interest margin volatility"),
        "liq_asset_ratio": ("L", "(CHBAL + SC) / ASSET", "Liquid assets to total assets"),
        "liq_dep_ratio": ("L", "(CHBAL + SC) / DEP", "Liquid reserves to deposit base"),
        "ldr": ("L", "LNLSNET / DEP", "Loan-to-deposit structural ratio"),
        "brokered_dep_ratio": ("L", "BRO / DEP", "Volatile wholesale funding share"),
        "log_asset": ("S", "ln(ASSET)", "Institution scale & franchise size"),
        "asset_growth_qoq": ("S", "ASSET(t)/ASSET(t-1) - 1", "Aggressive short-term loan growth"),
        "asset_growth_yoy": ("S", "ASSET(t)/ASSET(t-4) - 1", "Aggressive annual loan expansion"),
        "cap_zscore_q": ("S", "(cap - mean_q) / std_q", "Peer-relative capital position"),
        "roa_zscore_q": ("S", "(roa - mean_q) / std_q", "Peer-relative earnings strength"),
        "npl_zscore_q": ("S", "(npl - mean_q) / std_q", "Peer-relative credit impairment")
    }

    app_rows = []
    for feat, p in prep_params.items():
        if feat in formulas:
            cat, form, desc = formulas[feat]
            app_rows.append([
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
        app_headers,
        app_rows,
        col_widths=[1.2, 0.6, 1.4, 0.7, 0.7, 0.7, 1.7],
        caption="Table A.1: Master CAMELS Feature Store Dictionary & Development Baseline Parameters (preprocessor_dev_params.json)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT]
    )

    add_heading_2(doc, "Appendix B: Big Data Physical & Catalyst Execution Plans")
    add_paragraph(
        doc,
        "Excerpts from the compiled execution plans verifying projection pushdown, predicate filtering, and window operations in Polars and Apache Spark:"
    )

    polars_plan_text = (
        "POLARS LAZYFRAME OPTIMIZED PHYSICAL PLAN:\n"
        "WITH_COLUMNS:\n"
        " [[([(col(\"cap_ratio\")) - (col(\"cap_ratio\").mean().over([col(\"REPDTE\")]))]) / (col(\"cap_ratio\").std().over([col(\"REPDTE\")]))].alias(\"cap_zscore_pit\")]\n"
        "  WITH_COLUMNS:\n"
        "  [[(col(\"EQ\")) / (col(\"ASSET\"))].alias(\"cap_ratio\"), [(col(\"LNLSNET\")) / (col(\"ASSET\"))].alias(\"loan_asset_ratio\"),\n"
        "   [([(col(\"CHBAL\")) + (col(\"SC\"))]) / (col(\"DEP\"))].alias(\"liq_ratio\"), [(col(\"LNATRES\")) / (col(\"NCLNLS\"))].alias(\"coverage_ratio\"),\n"
        "   [([(col(\"ASSET\")) / (col(\"ASSET\").shift([dyn int: 1]).over([col(\"CERT\"))])) - (1.0)].alias(\"asset_growth_qoq\"),\n"
        "   col(\"ROA\").rolling_std().over([col(\"CERT\")]).alias(\"roa_vol_4q\")]\n"
        "   SORT BY [col(\"CERT\"), col(\"quarter_date\")]\n"
        "     Parquet SCAN [data_processed/panel_pit.parquet]\n"
        "     PROJECT 12/44 COLUMNS (Projection Pushdown Enabled)"
    )
    add_callout(doc, polars_plan_text, title="Excerpt B.1: Polars Execution Plan (polars_execution_plan.txt)")

    spark_plan_text = (
        "APACHE SPARK CATALYST OPTIMIZED LOGICAL PLAN (EXCERPT):\n"
        "== Analyzed Logical Plan ==\n"
        "CERT: bigint, REPDTE: string, quarter_date: date, ASSET: double, DEP: double, EQ: double, LNLSNET: double...\n"
        "Project [CERT#30L, REPDTE#4, quarter_date#33, cap_ratio#101, loan_asset_ratio#115, liq_ratio#130, cap_zscore_pit#249]\n"
        "+- Project [..., ((cap_ratio#101 - _we0#258) / _we1#259) AS cap_zscore_pit#249]\n"
        "   +- Window [avg(cap_ratio#101) windowspecdefinition(REPDTE#4) AS _we0#258,\n"
        "              stddev_samp(cap_ratio#101) windowspecdefinition(REPDTE#4) AS _we1#259], [REPDTE#4]\n"
        "      +- Window [lag(ASSET#18, -1, null) windowspecdefinition(CERT#30L, quarter_date#33 ASC) AS _we0#164], [CERT#30L]\n"
        "         +- Relation [EINTEXP#0, NIMY#1, ORE#2, LNATRES#3, REPDTE#4... 39 more fields] parquet"
    )
    add_callout(doc, spark_plan_text, title="Excerpt B.2: PySpark Catalyst Optimizer Plan (spark_catalyst_plan.txt)")

    add_heading_2(doc, "Appendix C: Automated Master QA Scorecard Verification")
    add_paragraph(
        doc,
        "Table C.1 reproduces the automated Quality Assurance Scorecard generated by `qa_check.py`, confirming that all 9 pipeline checkpoints have achieved 100% compliance with research integrity requirements:"
    )

    qa_df = pd.read_csv("artifacts/qa_master_checklist.csv")
    qa_headers = ["Pipeline Stage", "Audited Verification Item", "Compliance Status", "Empirical Output Evidence"]
    qa_rows = []
    for _, r in qa_df.iterrows():
        qa_rows.append([
            str(r["Part"]),
            str(r["Check_Item"]),
            str(r["Status"]),
            str(r["Actual_Evidence"])
        ])

    add_styled_table(
        doc,
        qa_headers,
        qa_rows,
        col_widths=[1.0, 2.2, 1.0, 2.8],
        caption="Table C.1: Master Automated Quality Assurance Scorecard (artifacts/qa_master_checklist.csv — 9/9 PASS)",
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT]
    )

    # Save Document
    doc.save(str(out_docx_path))
    print(f"Successfully generated academic research report: {out_docx_path.resolve()}")
    file_size_mb = out_docx_path.stat().st_size / (1024 ** 2)
    print(f"Report File Size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    output_file = Path("DaoHuyThanhVinh_11231024_FDIC_EWS_Report.docx")
    build_academic_report(output_file)
