from pathlib import Path
import zipfile
import hashlib
import re
import ast
import pandas as pd

root = Path.cwd()

print("\n=== 1. WORD REPORT INVENTORY ===")

docs = [
    p for p in root.glob("*.docx")
    if not p.name.startswith("~$")
]

for doc in docs:
    with zipfile.ZipFile(doc) as z:
        media = [
            n for n in z.namelist()
            if n.startswith("word/media/")
            and not n.endswith("/")
        ]
        print(
            f"{doc.name}: "
            f"{len(media)} embedded media files, "
            f"{doc.stat().st_size:,} bytes"
        )

print("\n=== 2. FINAL FIGURE INVENTORY ===")

figures = sorted(
    (root / "artifacts/figures").glob("fig*.png")
)

for p in figures:
    digest = hashlib.sha256(
        p.read_bytes()
    ).hexdigest()[:16]
    print(p.name, p.stat().st_size, digest)

print("\n=== 3. EXACT MATCH BETWEEN WORD AND NEW FIGURES ===")

figure_hashes = {
    hashlib.sha256(p.read_bytes()).hexdigest(): p.name
    for p in figures
}

for doc in docs:
    matches = []
    with zipfile.ZipFile(doc) as z:
        media = [
            n for n in z.namelist()
            if n.startswith("word/media/")
            and not n.endswith("/")
        ]
        for member in media:
            digest = hashlib.sha256(
                z.read(member)
            ).hexdigest()
            if digest in figure_hashes:
                matches.append(figure_hashes[digest])

    print(
        doc.name,
        "exactly matching new figures:",
        len(set(matches)),
        "/8"
    )
    print("Matched:", sorted(set(matches)))

print("\n=== 4. INSPECT MLLIB IMPLEMENTATION ===")

model_file = root / "src/fdic_pipeline/model.py"
source = model_file.read_text(encoding="utf-8-sig")
ast.parse(source)

for term in [
    "run_spark_mllib_demo",
    "train_count",
    "test_count",
    "areaUnderPR",
    "areaUnderROC",
    "spark_mllib_demo.csv"
]:
    print(f"{term}: {'FOUND' if term in source else 'NOT FOUND'}")

print("\n=== 5. INSPECT MODEL EVIDENCE FILES ===")

folder = root / "artifacts/model"

for p in sorted(folder.iterdir()):
    if p.is_file():
        print(f"{p.name}: {p.stat().st_size:,} bytes")

print("\n=== 6. GIT FILE SIZE AND BACKUP AUDIT ===")

for name in [
    "artifacts_backup",
    "data_reference",
    "docs",
    "logs",
    "scripts"
]:
    p = root / name
    if p.exists():
        files = [f for f in p.rglob("*") if f.is_file()]
        size = sum(f.stat().st_size for f in files)
        print(
            f"{name}: {len(files)} files, "
            f"{size/1048576:.2f} MiB"
        )

print("\nINSPECTION COMPLETE")
