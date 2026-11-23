from pathlib import Path
import subprocess
import zipfile
import re
import json
import urllib.request
import importlib.metadata as metadata
from xml.etree import ElementTree as ET

root = Path.cwd()
repo = "vinhong0506-coder/fdic-bank-risk-research"
problems = []

def check(label, ok, detail):
    print(f"[{'PASS' if ok else 'CHECK'}] {label}: {detail}")
    if not ok:
        problems.append(label)

print("\n=== A. PUBLIC GITHUB ===")
try:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"User-Agent": "FDIC-Submission-Audit"}
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        info = json.load(res)
    check(
        "GitHub Public",
        not info.get("private", True),
        info.get("html_url")
    )
except Exception as exc:
    check("GitHub Public", False, f"Cannot verify: {exc}")

print("\n=== B. REPORT COVER PAGE ===")
docs = [
    p for p in root.glob("*.docx")
    if not p.name.startswith("~$")
]
for doc in docs:
    try:
        with zipfile.ZipFile(doc) as z:
            xml = z.read("word/document.xml")
        tree = ET.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paras = []
        for p in tree.iter(ns + "p"):
            line = "".join(
                t.text or "" for t in p.iter(ns + "t")
            )
            if line.strip():
                paras.append(line.strip())

        # Read first 25 non-empty paragraphs for a cover audit.
        cover = "\n".join(paras[:25])
        found = "github.com/" in cover.lower()
        check("Cover GitHub URL", found, doc.name)
        print("COVER EXCERPT:")
        print(cover[:2000])
        print()
    except Exception as exc:
        check("Cover GitHub URL", False, str(exc))

print("\n=== C. README ===")
readme = root / "README.md"
text = readme.read_text(
    encoding="utf-8-sig"
) if readme.exists() else ""

check("README exists", bool(text.strip()), "README.md")
check(
    "README AI disclosure",
    bool(re.search(
        r"artificial intelligence|generative AI|AI-assisted|chatgpt|openai",
        text, re.I
    )),
    "Check genuine disclosure of AI tools used"
)
check(
    "README references",
    bool(re.search(
        r"references|data sources|citation|acknowledg",
        text, re.I
    )),
    "Check sources/citations section"
)

print("\n=== D. REQUIREMENTS ===")
reqfile = root / "requirements.txt"
check("requirements exists", reqfile.exists(), "requirements.txt")
if reqfile.exists():
    lines = [
        s.strip() for s in reqfile.read_text(
            encoding="utf-8-sig"
        ).splitlines()
        if s.strip() and not s.startswith("#")
    ]
    invalid = [s for s in lines if "==" not in s]
    print("Pinned packages:", len(lines))
    check("Pinned versions", not invalid, invalid[:8])

    for package in [
        "pandas", "polars", "pyarrow", "pyspark",
        "scikit-learn", "lightgbm", "matplotlib",
        "pytest"
    ]:
        try:
            print(package, metadata.version(package))
        except metadata.PackageNotFoundError:
            print(package, "NOT INSTALLED")

print("\n=== E. TRACKED DATA FILES ===")
proc = subprocess.run(
    ["git", "ls-files", "-z"],
    stdout=subprocess.PIPE, check=True
)
paths = [
    p for p in proc.stdout.decode(
        "utf-8", errors="replace"
    ).split("\0") if p
]
risky = [
    p for p in paths
    if p.lower().endswith((
        ".csv", ".parquet", ".xlsx", ".xls",
        ".zip", ".sqlite", ".db"
    ))
    or p.startswith(("data_raw/", "data_processed/"))
]
check(
    "No tracked data files",
    not risky,
    f"{len(risky)} potentially prohibited tracked files"
)
for p in risky[:60]:
    print("TRACKED:", p)

print("\n=== F. SOURCE AND TESTS ===")
source = list((root / "src").rglob("*.py"))
tests = list((root / "tests").glob("test_*.py"))
check("Source files", bool(source), f"{len(source)} Python files")
check("Test files", bool(tests), f"{len(tests)} test files")

print("\n=== SUMMARY ===")
print("Items requiring review:", len(problems))
for item in problems:
    print("REVIEW:", item)
print("AUDIT COMPLETE")
