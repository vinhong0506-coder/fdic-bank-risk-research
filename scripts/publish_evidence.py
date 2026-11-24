"""Copy selected small, inspectable evidence into tracked docs/evidence.
No row-level predictions, datasets, logs with secrets, or large files copied.
"""
from pathlib import Path
import shutil
SOURCES = [
 'artifacts/audit/panel_flow.json',
 'artifacts/audit/failure_reconciliation.json',
 'artifacts/audit/temporal_split_summary.csv',
 'artifacts/audit/capital_availability_by_year.csv',
 'artifacts/benchmark/storage_full/storage_benchmark.csv',
 'artifacts/benchmark/engine/numeric_equivalence.json',
 'artifacts/benchmark/engine/benchmark_summary.csv',
 'artifacts/model/empirical_cost_estimation.csv',
 'artifacts/model/dev_timeseries_cv.csv',
 'artifacts/model/frozen_development_decisions.json',
 'artifacts/model/final_test_metrics.csv',
 'artifacts/model/regime_nonadditivity.json',
 'artifacts/model/cost_assumption_sensitivity.csv',
 'artifacts/qa/qa_checklist.csv',
]
def main():
    dest=Path('docs/evidence');dest.mkdir(parents=True,exist_ok=True)
    copied=[]; missing=[]
    for name in SOURCES:
        src=Path(name)
        if not src.exists():missing.append(name);continue
        if src.stat().st_size>2_000_000:
            raise ValueError(f'Refusing oversized evidence: {name}')
        target=dest/(name.replace('/','__'))
        shutil.copyfile(src,target);copied.append(str(target))
    (dest/'INVENTORY.md').write_text('# Generated evidence snapshots\n\n'
           'These files must be regenerated from the exact submitted code commit. '
           'Do not interpret file existence as validation.\n\n'
           + '\n'.join('- '+p for p in copied)
           + '\n\nMissing:\n' + '\n'.join('- '+p for p in missing),encoding='utf-8')
    print(f'Copied {len(copied)} files; missing {len(missing)}')
if __name__=='__main__':main()
