
"""Verify or reproduce the current FDIC publication figures."""
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

NAMES = [
    "fig1_storage_benchmark.png",
    "fig2_capital_regime_audit.png",
    "fig3_temporal_split_overview.png",
    "fig4_engine_benchmark_1x.png",
    "fig5_synthetic_scaling_5x.png",
    "fig6_test_pr_and_calibration.png",
    "fig7_top10_camels_importance.png",
    "fig8_cost_and_regime_analysis.png",
]

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check():
    mpath = ROOT / "docs/evidence/verified_figures_manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    hashes = manifest.get("figures_sha256", {})

    if set(hashes) != set(NAMES):
        raise RuntimeError("Unexpected figure manifest")

    if manifest.get("benchmark_runs") != 27:
        raise RuntimeError("Wrong benchmark version")

    if manifest.get("data_label_count") != 80:
        raise RuntimeError("Wrong figure label count")

    for name in NAMES:
        p = ROOT / "docs/figures" / name
        if not p.is_file() or p.stat().st_size < 1000:
            raise FileNotFoundError(p)
        if digest(p) != hashes[name]:
            raise RuntimeError("Figure SHA256 mismatch: " + name)

    print("CURRENT_FIGURES: PASS (8/8)")
    print("Benchmark maximum: 5x")
    print("Published figure hashes: VERIFIED")

def rebuild():
    source = ROOT / "scripts/generate_stageD_labeled.py"
    text = source.read_text(encoding="utf-8-sig")

    marker = 'out = root / "artifacts/stageD/figures_labeled"'
    if text.count(marker) != 1:
        raise RuntimeError("Unexpected figure generator version")

    label = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = f"figures_rebuilt_{label}"

    text = text.replace(
        marker,
        f'out = root / "artifacts/stageD/{folder}"',
        1
    )

    text = text.replace(
        'out.parent / "figures_labeled_manifest.json"',
        f'out.parent / "{folder}_manifest.json"'
    )

    tmp = ROOT / "logs/figure_rebuild"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / f"rebuild_{label}.py"
    script.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script)], cwd=ROOT
    )
    if result.returncode:
        raise RuntimeError("Figure rebuild failed")

    target = ROOT / "artifacts/stageD" / folder
    generated = {p.name for p in target.glob("fig*.png")}

    if generated != set(NAMES):
        raise RuntimeError("Incomplete regenerated figures")

    print("REBUILT_FIGURES: PASS")
    print("NEW OUTPUT:", target)
    print("Published figures were not overwritten")

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    if args.rebuild:
        rebuild()
    else:
        check()

if __name__ == "__main__":
    main()
