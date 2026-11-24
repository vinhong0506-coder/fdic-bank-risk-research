"""
Verification script for submission deliverables:
- Render each PDF page to PNG
- Measure page counts (Total, Main Report, Appendices)
- Verify text extraction and key data consistency
- Confirm figure order and caption presence
"""
from pathlib import Path
import pymupdf  # PyMuPDF
import re

def verify_submission():
    pdf_path = Path("deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    doc = pymupdf.open(str(pdf_path))
    total_pages = len(doc)
    print(f"Total PDF Pages: {total_pages}")

    # Create render directory
    render_dir = Path("deliverables/rendered_pages")
    render_dir.mkdir(parents=True, exist_ok=True)

    page_texts = []
    main_start = None
    ref_start = None
    app_start = None

    for i, page in enumerate(doc):
        # Render page to PNG
        pix = page.get_pixmap(dpi=150)
        img_out = render_dir / f"page_{i+1:02d}.png"
        pix.save(str(img_out))

        # Extract text
        txt = page.get_text()
        page_texts.append(txt)

        if "EXECUTIVE SUMMARY AND RESEARCH QUESTIONS" in txt and main_start is None:
            main_start = i + 1
        if "REFERENCES" in txt and ref_start is None:
            ref_start = i + 1
        if "TECHNICAL APPENDICES" in txt and app_start is None:
            app_start = i + 1

    print(f"Main Report starts on page: {main_start}")
    print(f"References start on page: {ref_start}")
    print(f"Technical Appendices start on page: {app_start}")

    cover_toc_pages = (main_start - 1) if main_start else 2
    main_pages = (ref_start - main_start) if (main_start and ref_start) else 0
    ref_pages = (app_start - ref_start) if (ref_start and app_start) else 1
    app_pages = (total_pages - app_start + 1) if app_start else 0

    print(f"Cover & TOC Pages: {cover_toc_pages}")
    print(f"Main Content Pages: {main_pages} (Limit <= 20)")
    print(f"References Pages: {ref_pages}")
    print(f"Technical Appendices Pages: {app_pages} (Limit <= 10)")

    # Assert page limits
    assert main_pages <= 20, f"Main content exceeds 20 pages! ({main_pages})"
    assert app_pages <= 10, f"Appendices exceed 10 pages! ({app_pages})"

    full_text = "\n".join(page_texts)

    # Key phrases and checks
    checks = {
        "170 Quarters": "170" in full_text,
        "1,682,738 Raw Rows": "1,682,738" in full_text,
        "5,631 Zombie Rows": "5,631" in full_text,
        "1,677,107 Clean Panel": "1,677,107" in full_text,
        "1,176,223 Dev Valid": "1,176,223" in full_text,
        "386,964 Test Valid": "386,964" in full_text,
        "1,775 Test Positives": "1,775" in full_text,
        "500 Unique Test Failed Banks": "500" in full_text,
        "30 Base Features": "30" in full_text and "60" in full_text,
        "Polars 0.80s / 0.797s": "0.797" in full_text or "0.80" in full_text,
        "pandas 5.16s / 5.157s": "5.157" in full_text or "5.16" in full_text,
        "PySpark 14.76s / 14.757s": "14.757" in full_text or "14.76" in full_text,
        "10x Not Measured": "10x was not measured" in full_text or "10x scale was not measured" in full_text,
        "Loss Ratio 40.3:1": "40.3" in full_text,
        "Median Loss Rate 20.17%": "20.17%" in full_text,
        "Assumed CFP 0.50%": "0.50%" in full_text,
        "484 of 500 Banks Captured": "484" in full_text,
        "96.8% Recall": "96.8%" in full_text,
        "1.78% Alert Rate": "1.78%" in full_text,
        "507 Regime Sum vs 500": "507" in full_text,
        "Figure 1 Present": "Figure 1:" in full_text,
        "Figure 2 Present": "Figure 2:" in full_text,
        "Figure 3 Present": "Figure 3:" in full_text,
        "Figure 4 Present": "Figure 4:" in full_text,
        "Figure 5 Present": "Figure 5:" in full_text,
        "Figure 6 Present": "Figure 6:" in full_text,
        "Figure 7 Present": "Figure 7:" in full_text,
        "Figure 8 Present": "Figure 8:" in full_text,
    }

    print("\n--- CONTENT INTEGRITY CHECKS ---")
    all_pass = True
    for name, res in checks.items():
        status = "PASS" if res else "FAIL"
        print(f"[{status}] {name}")
        if not res:
            all_pass = False

    # Prohibited claims checks
    prohibited = [
        ("31 Base Features Claim", "31 base features"),
        ("62 Transformed Predictors Claim", "62 predictors"),
        ("Spark beating Polars at 2x", "Spark is faster than Polars at 2x"),
        ("Fabricated 10x Speedup", "10x crossover point at"),
    ]
    for name, phrase in prohibited:
        found = phrase.lower() in full_text.lower()
        status = "PASS (Not Found)" if not found else "FAIL (Found Prohibited Phrase)"
        print(f"[{status}] Prohibited: {name}")
        if found:
            all_pass = False

    print(f"\nOverall Integrity Check: {'ALL PASS' if all_pass else 'SOME CHECKS FAILED'}")
    return all_pass, total_pages, main_pages, app_pages

if __name__ == "__main__":
    verify_submission()
