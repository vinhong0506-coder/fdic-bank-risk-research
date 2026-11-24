from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, confusion_matrix
from fdic_pipeline.features import SELECTED_CAMELS_FEATURES
from fdic_pipeline.model import BASE_FEATURES

root = Path.cwd()
model = root / 'artifacts/model_30feature_corrected'
bench = root / 'artifacts/stageC/final'
fig = root / 'artifacts/stageD/figures_labeled'
checks = []

def check(name, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    checks.append((name, status, str(detail)))
    print(f'[{status}] {name}: {detail}', flush=True)

def warn(name, detail):
    checks.append((name, 'WARN', str(detail)))
    print(f'[WARN] {name}: {detail}', flush=True)

try:
    frozen = json.loads((model/'frozen_development_decisions.json').read_text(encoding='utf-8'))
    base = list(SELECTED_CAMELS_FEATURES)
    dictionary = pd.read_csv(root/'artifacts/features/feature_dictionary.csv')['feature'].astype(str).tolist()
    check('FEATURE_CONTRACT',len(base)==30 and base==BASE_FEATURES==dictionary==frozen['feature_cols'], '30 base features, 60 predictors')

    old = pd.read_parquet(model/'test_predictions.parquet',columns=['target_4q','prob_lr','prob_lgb'])
    y = old.target_4q.astype(int).to_numpy()
    reported = pd.read_csv(model/'final_test_metrics.csv')
    check('TEST_POPULATION',len(y)==386964 and int(y.sum())==1775, f'rows={len(y)}, positives={int(y.sum())}')
    for title,col in [('Logistic Regression','prob_lr'),('LightGBM','prob_lgb')]:
        pr = float(average_precision_score(y,old[col]));roc = float(roc_auc_score(y,old[col]))
        row = reported[(reported.Model==title) & reported.Dataset.astype(str).str.startswith('Full Test')]
        ok = len(row)==1 and abs(float(row.iloc[0].PR_AUC)-pr)<0.000051 and abs(float(row.iloc[0].ROC_AUC)-roc)<0.000051
        check('CORRECTED_'+title,ok,f'AP={pr:.6f}; ROC={roc:.6f}')

    cost = pd.read_csv(model/'test_cost_sensitive_decisions.csv')
    discrepancies = []
    for r in cost.itertuples(index=False):
        cfg = frozen['thresholds'].get(r.Scenario)
        if cfg is None or r.Model not in ('Logistic Regression','LightGBM'):
            discrepancies.append((r.Scenario,r.Model,'unknown'));continue
        key,col = ('tau_lr','prob_lr') if r.Model=='Logistic Regression' else ('tau_lgb','prob_lgb')
        tau,ratio=float(cfg[key]),float(cfg['cost_ratio'])
        tn,fp,fn,tp=confusion_matrix(y,(old[col].to_numpy()>=tau).astype(int),labels=[0,1]).ravel()
        if (tp,fp,fn)!=(int(r.TP),int(r.FP),int(r.FN)) or abs(float(r.Frozen_Tau)-tau)>0.000051 or abs(float(r.Expected_Cost_Units)-(ratio*fn+fp))>0.11:
            discrepancies.append((r.Scenario,r.Model,'mismatch'))
    check('FROZEN_OOF_THRESHOLDS_COST',len(cost)==6 and not discrepancies,repr(discrepancies))

    ml = pd.read_csv(model/'spark_mllib_demo.csv')
    manifest = json.loads((model/'spark_mllib_validation.json').read_text(encoding='utf-8'))
    pred_path=root/manifest['prediction_parquet_dir']
    s=pd.read_parquet(pred_path,columns=['label','prob_failure'])
    ys=s.label.astype(int).to_numpy(); ps=s.prob_failure.to_numpy(dtype=float)
    mlok = (len(ml)==1 and 'Status' not in ml.columns and int(ml.iloc[0].Train_Rows)==1176223
            and int(ml.iloc[0].Test_Rows)==386964 and int(ml.iloc[0].Num_Features)==60
            and len(ys)==386964 and int(ys.sum())==1775 and np.isfinite(ps).all()
            and (ps>=0).all() and (ps<=1).all())
    check('SPARK_MLLIB_SAVED_PREDICTIONS',mlok,f'rows={len(ys)}, features={int(ml.iloc[0].Num_Features)}')
    pr_sklearn = float(average_precision_score(ys,ps))
    roc_sklearn = float(roc_auc_score(ys,ps))
    proof = abs(pr_sklearn-manifest['sklearn_average_precision'])<1e-10 and abs(roc_sklearn-manifest['sklearn_roc_auc'])<1e-10
    summary_consistent = abs(float(ml.iloc[0].Test_PR_AUC)-float(manifest['spark_areaUnderPR']))<0.000051 and abs(float(ml.iloc[0].Test_ROC_AUC)-float(manifest['spark_areaUnderROC']))<0.000051
    check('SPARK_MLLIB_INDEPENDENT_RESCORE',proof and summary_consistent,f'Spark PR={manifest["spark_areaUnderPR"]:.6f}, sklearn AP={pr_sklearn:.6f}; ROC={roc_sklearn:.6f}')

    runs=pd.read_csv(bench/'benchmark_runs.csv')
    expected={(engine,scale,run) for engine in ('pandas','polars','spark') for scale in (1,2,5) for run in (1,2,3)}
    grid=set(zip(runs.engine,runs.scale.astype(int),runs.run.astype(int)))
    check('BENCHMARK_27',len(runs)==27 and grid==expected, f'27/27 completed, 10x not measured')
    summary=pd.read_csv(bench/'benchmark_summary.csv')
    med=runs.groupby(['scale','engine']).wall_seconds.median()
    median_ok=all(abs(float(r.median_wall_seconds)-float(med.loc[(int(r.scale),r.engine)]))<1e-6 for r in summary.itertuples(index=False))
    check('BENCHMARK_MEDIANS',median_ok,'Median values from raw runs')

    names=['fig1_storage_benchmark.png','fig2_capital_regime_audit.png','fig3_temporal_split_overview.png',
           'fig4_engine_benchmark_1x.png','fig5_synthetic_scaling_5x.png',
           'fig6_test_pr_and_calibration.png','fig7_top10_camels_importance.png','fig8_cost_and_regime_analysis.png']
    labels=pd.read_csv(fig/'figure_data_labels.csv')
    fig_ok=(all((fig/n).is_file() and (fig/n).stat().st_size>1000 for n in names)
            and set(labels.figure)==set(names) and len(labels)>=80)
    check('FIGURES_LABELED_8',fig_ok,f'{len(labels)} data labels across 8 images')
    lifecycle=pd.read_csv(root/'artifacts/stageB/audit/lifecycle_conflict_impact.csv')
    life_ok = lifecycle.CERT.nunique()==29 and int(lifecycle.positive_bq.sum())==106 and int(lifecycle.test_positive_bq.sum())==0
    check('LIFECYCLE_IMPACT_COUNT',life_ok, '29 CERTs, 106 positive bank-quarters, 0 positive in TEST')
except Exception as exc:
    check('AUDIT_EXCEPTION',False,repr(exc))

warn('LIFECYCLE_EVENT_ADJUDICATION','Exit mapping/ENDEFYMD conflicts not fully adjudicated')
warn('BENCHMARK_10X','Not run on current hardware; report only 1x, 2x, 5x')
warn('FIGURE_VISUAL_INSPECTION','Review label overlap and captions visually')
warn('REPORT_README_GITHUB','Update report, README, audited evidence and GitHub links')

report=pd.DataFrame(checks,columns=['Check','Status','Details'])
out=root/'logs/stageE';out.mkdir(parents=True,exist_ok=True)
report.to_csv(out/'stageE_final_verified.csv',index=False)
print('\n=== STAGE E FINAL VERIFIED ===')
print(report.to_string(index=False))
print('PASS:',int(report.Status.eq('PASS').sum()),'WARN:',int(report.Status.eq('WARN').sum()),'FAIL:',int(report.Status.eq('FAIL').sum()))
print('OUTPUT:',out/'stageE_final_verified.csv')
if report.Status.eq('FAIL').any():
    raise SystemExit(1)
print('STAGE_E_TECHNICAL: PASS; RESEARCH WARNINGS REMAIN')
