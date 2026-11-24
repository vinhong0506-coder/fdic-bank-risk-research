"""Conservative, opt-in source patch for FDIC EWS stage B.

Only performs two localized changes, using exact independently-reviewed patterns.
Refuses unknown source forms. Does not touch data or model outputs.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime
import difflib
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
# Roots are calculated relative to the folder into which this file is copied: repo/scripts.


def change_features(src: str) -> tuple[str,str]:
    old = "    pl.from_pandas(final_df).write_parquet(out_parquet, compression='zstd')"
    # Polars 2.1 yields ns timestamps for pandas datetime64[ns], which Spark 3.5
    # may reject (INT64 TIMESTAMP(NANOS)); convert before Parquet write.
    new = '''    spark_safe = pl.from_pandas(final_df)
    ns_cols = [name for name, dtype in spark_safe.schema.items()
               if dtype == pl.Datetime('ns')]
    if ns_cols:
        spark_safe = spark_safe.with_columns(
            [pl.col(name).dt.cast_time_unit('us') for name in ns_cols]
        )
    spark_safe.write_parquet(out_parquet, compression='zstd')'''
    if old in src:
        if src.count(old) != 1:
            raise ValueError("More than one Parquet writer matched")
        return src.replace(old, new), 'PATCH_FEATURE_TIMESTAMP_US'
    if 'spark_safe.write_parquet(out_parquet' in src and "cast_time_unit('us')" in src:
        return src, 'ALREADY_PATCHED_FEATURE_TIMESTAMP_US'
    raise ValueError('Unrecognized feature Parquet writer; refusing to overwrite local custom changes')


def ensure_early_test_guard(src: str) -> tuple[str,str]:
    """Protect frozen Test results before ANY artifacts are written."""
    header = "def run_modeling_pipeline(pit_path: Path, raw_dir: Path, out_dir: Path) -> None:\n"
    old = header + "    out_dir.mkdir(parents=True, exist_ok=True)"
    new = (header
           + '    if (out_dir / "final_test_metrics.csv").exists():\n'
           + '        raise RuntimeError("Frozen Test artifacts exist; archive explicitly before rerunning")\n'
           + "    out_dir.mkdir(parents=True, exist_ok=True)")
    if old in src:
        return src.replace(old,new,1),'PATCH_EARLY_TEST_GUARD'
    if new in src:
        return src,'ALREADY_EARLY_TEST_GUARD'
    raise ValueError('Unrecognized run_modeling_pipeline entry; will not modify Test locking')


def change_model(src: str) -> tuple[str,str]:
    old = '''    except Exception as exc:
        pd.DataFrame([{"Status": f"SKIPPED: {exc}"}]).to_csv(out_dir / "spark_mllib_demo.csv", index=False)'''
    new = '''    except Exception as exc:
        # Never turn an MLlib execution failure into an apparently successful run.
        pd.DataFrame([{"Status": f"FAILED: {exc}"}]).to_csv(
            out_dir / "spark_mllib_demo.csv", index=False
        )
        raise RuntimeError("Spark MLlib failed: inspect spark_mllib_demo.csv") from exc'''
    if old in src:
        if src.count(old) != 1:
            raise ValueError("More than one MLlib handler matched")
        res,guard_status=ensure_early_test_guard(src.replace(old,new))
        return res, 'PATCH_MLLIB_FAIL_CLOSED, '+guard_status
    # Explicitly detect an existing fail-closed handler rather than duplicating it.
    try:
        tree=ast.parse(src)
    except SyntaxError as exc:
        raise ValueError(f'Python syntax invalid in model.py: {exc}') from exc
    fn=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='run_spark_mllib_demo'),None)
    if fn:
        for n in ast.walk(fn):
            if isinstance(n,ast.ExceptHandler):
                source_segment='\n'.join(src.splitlines()[n.lineno-1:n.end_lineno])
                if 'spark_mllib_demo.csv' in source_segment and any(isinstance(x,ast.Raise) for x in ast.walk(n)):
                    res,guard_status=ensure_early_test_guard(src)
                    return res, 'ALREADY_FAIL_CLOSED, '+guard_status
    raise ValueError('Unrecognized MLlib exception handler; refusing to overwrite local custom changes')


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check',action='store_true')
    g.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    paths={
        ROOT/'src/fdic_pipeline/features.py':change_features,
        ROOT/'src/fdic_pipeline/model.py':change_model,
    }
    pending={}
    try:
        for path,fn in paths.items():
            if not path.exists(): raise FileNotFoundError(path)
            original=path.read_text(encoding='utf-8-sig')
            proposed,status=fn(original)
            ast.parse(proposed,filename=str(path))
            pending[path]=(original,proposed,status)
            print(path.relative_to(ROOT),status)
            if proposed!=original:
                diff=difflib.unified_diff(original.splitlines(),proposed.splitlines(),fromfile=str(path)+' (before)',tofile=str(path)+' (after)',lineterm='')
                print('\n'.join(diff))
    except (ValueError,FileNotFoundError,SyntaxError) as exc:
        print(f'ABORT_NO_CHANGES: {exc}',file=sys.stderr)
        return 2
    if args.check:
        print('DRY_RUN_PASS: No source file changed')
        return 0
    changes={path:(old,new) for path,(old,new,_) in pending.items() if old!=new}
    if not changes:
        print('ALREADY_PATCHED: No action necessary')
        return 0
    backup=ROOT/'artifacts/diagnostics/stageB_source_backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True,exist_ok=False)
    # Back up ALL changed files before changing ANY files.
    for path in changes:
        target=backup/path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    try:
        for path,(_,proposed) in changes.items():
            tmp=path.with_name(path.name+'.stageB.tmp')
            tmp.write_text(proposed,encoding='utf-8')
            ast.parse(tmp.read_text(encoding='utf-8'),filename=str(path))
            tmp.replace(path)
            print('PATCHED',path.relative_to(ROOT))
    except Exception:
        for path in changes:
            shutil.copy2(backup/path.relative_to(ROOT),path)
        print('RESTORED_FROM_BACKUPS',backup,file=sys.stderr)
        raise
    print('PATCH_OK; BACKUPS:',backup)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
