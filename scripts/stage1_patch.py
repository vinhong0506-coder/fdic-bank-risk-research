"""Conservative FDIC compatibility + DEV-only feature-selection patch.

Run from repository root: python scripts/stage1_patch.py --check / --apply
Does NOT touch data, artifacts/model, or Git. Saves a timestamped copy of each
modified source file before making a change.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "src/fdic_pipeline/features.py": {
        "rolling_std(window_size=4, min_periods=4, ddof=1)": "rolling_std(window_size=4, min_samples=4, ddof=1)",
        "feature_cols = [c for c in candidate_feats if c in raw_feat_df.columns and raw_feat_df[c].null_count() < raw_feat_df.height]": (
            'dev_valid_features = raw_feat_df.filter(\n'
            '        (pl.col("split") == "DEV") & pl.col("target_4q").is_not_null()\n'
            '    )\n'
            '    feature_cols = [\n'
            '        c for c in candidate_feats\n'
            '        if c in dev_valid_features.columns\n'
            '        and dev_valid_features[c].null_count() < dev_valid_features.height\n'
            '    ]'
        ),
    },
    "src/fdic_pipeline/workload.py": {"rolling_std(window_size=4, min_periods=4, ddof=1)": "rolling_std(window_size=4, min_samples=4, ddof=1)"},
    "src/fdic_pipeline/model.py": {
        "feat_cols = [c for c in BASE_FEATURES if c in raw_df.columns]": (
            'dev_feature_mask = (raw_df["split"] == "DEV") & raw_df["target_4q"].notna()\n'
            '    feat_cols = [\n'
            '        c for c in BASE_FEATURES\n'
 '        if c in raw_df.columns and raw_df.loc[dev_feature_mask, c].notna().any()\n'
            '    ]'
        ),
    },
}


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="show required changes, do not edit")
    mode.add_argument("--apply", action="store_true", help="back up and apply exact changes")
    args = ap.parse_args()

    updates: dict[Path, str] = {}
    errors: list[str] = []
    for relative, replacements in FILES.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"SOURCE_MISSING: {relative}")
            continue
        old = path.read_text(encoding="utf-8-sig")
        updated = old
        print(f"FILE: {relative}")
        for before, after in replacements.items():
            original_occurrences = updated.count(before)
            if original_occurrences:
                updated = updated.replace(before, after)
                print(f"  PATCH needed: {before[:65]} ({original_occurrences} occurrences)")
            elif after in updated:
                print(f"  Already patched: {before[:65]}")
            else:
                errors.append(f"UNEXPECTED_SOURCE: {relative}; missing pattern: {before[:100]}")
        if updated != old:
            # Verify syntax before touching source.
            compile(updated, str(path), "exec")
            updates[path] = updated
    if errors:
        for e in errors:
            print("ERROR:", e)
        print("ABORT: no source files changed.")
        return 2
    if args.check:
        print(f"DRY_RUN_OK: {len(updates)} files would be changed. Use --apply to back up and apply.")
        return 0
    if not updates:
        print("ALREADY_PATCHED: no changes required.")
        return 0

    backup_dir = ROOT / "artifacts" / "diagnostics" / "stage1_patch_backups" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    for path in updates:
        dest = backup_dir / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    print("BACKUP:", backup_dir)
    for path, content in updates.items():
        path.write_text(content, encoding="utf-8")
        print("PATCHED:", path.relative_to(ROOT))
    print("PATCH_OK: compatibility + DEV-only feature selection updated. Lifecycle labels NOT changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
