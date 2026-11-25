from __future__ import annotations
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT = ROOT / 'artifacts' / 'prepush_qa' / STAMP
OUT.mkdir(parents=True, exist_ok=True)
checks = []


def record(name, status, detail):
    assert status in ('PASS', 'WARN', 'FAIL')
    checks.append({'check': name, 'status': status, 'detail': str(detail)})
    print(f'[{status}] {name}: {detail}', flush=True)


def command(name, args, timeout=600, success_text=None):
    try:
        p = subprocess.run(args, cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace',
                           timeout=timeout)
        msg = (p.stdout or '') + '\n--- STDERR ---\n' + (p.stderr or '')
        (OUT / f'{name}.log').write_text(msg, encoding='utf-8')
        ok = p.returncode == 0 and (success_text is None or success_text in msg)
        record(name, 'PASS' if ok else 'FAIL',
               f'exit={p.returncode}; see artifacts/prepush_qa/{STAMP}/{name}.log')
        if not ok:
            print('\n'.join(msg.splitlines()[-8:]), flush=True)
        return p
    except Exception as exc:
        record(name, 'FAIL', f'{type(exc).__name__}: {exc}')
        return None


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def audit_quarters():
    manifest = ROOT / 'data_raw/fdic/manifest_financials.json'
    if not manifest.is_file():
        record('FDIC_170_SHA256', 'WARN', f'Missing local manifest: {manifest}')
        return False
    try:
        obj = json.loads(manifest.read_text(encoding='utf-8-sig'))
        if not isinstance(obj, dict):
            raise TypeError('Manifest is not a dictionary')
        expected = {}
        for year in range(1984, 2027):
            for quarter, (month, day) in enumerate(((3, 31), (6, 30), (9, 30), (12, 31)), 1):
                if (year, quarter) > (2026, 2):
                    continue
                key = f'{year}{month:02d}{day:02d}'
                expected[key] = ROOT / f'data_raw/fdic/financials/YEAR={year}/QUARTER=Q{quarter}/REPDTE={key}.parquet'
        rows = []
        for key, path in expected.items():
            entry = obj.get(key)
            if not isinstance(entry, dict):
                rows.append({'quarter': key, 'rows': '', 'sha256': '', 'status': 'MISSING_MANIFEST_ENTRY'})
                continue
            saved = str(entry.get('sha256', '')).lower()
            if not re.fullmatch(r'[0-9a-f]{64}', saved):
                rows.append({'quarter': key, 'rows': entry.get('rows', ''), 'sha256': '', 'status': 'INVALID_SAVED_SHA'})
                continue
            if not path.is_file():
                rows.append({'quarter': key, 'rows': entry.get('rows', ''), 'sha256': saved, 'status': 'FILE_MISSING'})
                continue
            actual = hash_file(path)
            metadata_ok = (entry.get('complete') is True
                           and int(entry.get('rows', -1)) == int(entry.get('api_total', -2))
                           and int(entry.get('duplicate_keys', -1)) == 0)
            status = 'PASS' if actual == saved and metadata_ok else 'MISMATCH'
            rows.append({'quarter': key, 'rows': entry.get('rows', ''),
                         'sha256': actual, 'status': status})
        with (OUT / 'quarter_sha256_results.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['quarter', 'rows', 'sha256', 'status'])
            writer.writeheader()
            writer.writerows(rows)
        count_pass = sum(r['status'] == 'PASS' for r in rows)
        total_rows = sum(int(r['rows']) for r in rows if r['status'] == 'PASS')
        good = len(obj) == 170 and len(expected) == 170 and count_pass == 170 and total_rows == 1682738
        record('FDIC_170_SHA256', 'PASS' if good else 'FAIL',
               f'valid={count_pass}/170; manifest_entries={len(obj)}; rows_pass={total_rows:,}; original manifest not rewritten')
        if good:
            destination = ROOT / 'docs/evidence' / f'quarter_sha256_independent_{datetime.now():%Y%m%d}.md'
            destination.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                '# Independent local SHA-256 recheck of FDIC quarterly files', '',
                f'Audit date: {datetime.now():%Y-%m-%d}.',
                'Source: `data_raw/fdic/manifest_financials.json` (not committed).',
                'Method: recompute SHA-256 from each existing local Parquet file; compare to stored manifest checksum, completeness, row count and duplicates.',
                f'**PASS: 170/170 quarters; total rows from verified manifest entries: {total_rows:,}.**',
                'This verifies **local file integrity against the stored manifest**, not a fresh download, historical API vintage, or external FDIC provenance.', '',
                '| REPDTE | Rows | Recomputed SHA-256 | Status |',
                '|---|---:|---|---|',
            ]
            lines.extend(f"| {r['quarter']} | {r['rows']} | `{r['sha256']}` | {r['status']} |" for r in rows)
            destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            record('SHA_PUBLIC_EVIDENCE', 'PASS', str(destination.relative_to(ROOT)))
        return good
    except Exception as exc:
        record('FDIC_170_SHA256', 'FAIL', f'{type(exc).__name__}: {exc}')
        return False


def audit_documents():
    pdf = ROOT / 'deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf'
    docx = pdf.with_suffix('.docx')
    record('DELIVERABLE_FILES', 'PASS' if pdf.is_file() and docx.is_file() else 'FAIL',
           f'PDF={pdf.is_file()}; DOCX={docx.is_file()}')
    if pdf.is_file():
        try:
            import pymupdf
            with pymupdf.open(pdf) as d:
                n = len(d)
                body = '\n'.join(page.get_text() for page in d)
            ok = n == 24 and '0.03219' in body and '0.02008' in body
            record('PDF_24_PAGES_CV_OOF', 'PASS' if ok else 'WARN',
                   f'pages={n}; LR corrected threshold present={"0.03219" in body}; LGB threshold present={"0.02008" in body}')
        except ImportError:
            record('PDF_24_PAGES_CV_OOF', 'WARN', 'pymupdf unavailable; skipped')
        except Exception as exc:
            record('PDF_24_PAGES_CV_OOF', 'FAIL', f'{type(exc).__name__}: {exc}')
    readme = ROOT / 'README.md'
    if readme.exists():
        s = readme.read_text(encoding='utf-8')
        stale = [x for x in ('23 pages overall', '17 pages of main analysis', '13 passing unit tests') if x in s]
        record('README_CURRENT_VERSION', 'WARN' if stale else 'PASS',
               'Stale text: ' + '; '.join(stale) if stale else 'No known old page/test counts detected')
    else:
        record('README_CURRENT_VERSION', 'FAIL', 'README.md missing')
    statuses = [ROOT / 'docs/evidence/part5_integrity_status.json', ROOT / 'docs/evidence/final_verified_results_20261124.md']
    for p in statuses:
        if p.exists() and ('NOT_INDEPENDENTLY_VERIFIED' in p.read_text(encoding='utf-8') or 'Update Word report tables' in p.read_text(encoding='utf-8')):
            record('STALE_EVIDENCE_NOTE', 'WARN', f'Review outdated wording: {p.relative_to(ROOT)}')


def git_audit():
    p = subprocess.run(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
                       cwd=ROOT, capture_output=True)
    if p.returncode:
        record('GIT_STATUS', 'FAIL', p.stderr.decode(errors='replace')[-250:])
        return
    entries = p.stdout.split(b'\0')
    changed = []
    i = 0
    while i < len(entries):
        raw = entries[i]
        i += 1
        if not raw:
            continue
        s = raw.decode('utf-8', errors='replace')
        if len(s) < 4:
            continue
        code, path = s[:2], s[3:]
        if 'R' in code or 'C' in code:
            i += 1  # porcelain -z has a second path for rename/copy
        changed.append((code, path))
    (OUT / 'git_changed_files.txt').write_text('\n'.join(f'{code} {name}' for code, name in changed), encoding='utf-8')
    record('GIT_STATUS', 'PASS', f'{len(changed)} changed/untracked files; see git_changed_files.txt')
    # Suggested staging is curated and NOT executed.
    exact = {
        'README.md', '.gitignore',
        'src/fdic_pipeline/model.py',
        'src/fdic_pipeline/export_submission_docx.py',
        'scripts/verify_submission_deliverables.py',
        'scripts/audit_fix_fdic_cv.py',
        'scripts/_fdic_lgb_worker.py',
        'scripts/prepush_qa_fdic.py',
        'tests/test_cv_feature_local_guard.py',
        'tests/test_fold_local_feature_selection.py',
        'deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx',
        'deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf',
        'deliverables/report_validation.md',
        'deliverables/rubric_compliance_matrix.md',
        'deliverables/targeted_corrections_log.md',
        'docs/evidence/cv_feature_availability_audit.md',
    }
    curated = [p for _, p in changed if p.replace('\\', '/') in exact
               or p.replace('\\', '/').startswith('docs/evidence/cv_fold_local_impact_')
               or p.replace('\\', '/').startswith('docs/evidence/quarter_sha256_independent_')]
    plan = ['# REVIEW every file before using any git add command',
            '# Do NOT stage deliverables/backup, rendered_pages or artifacts']
    plan += ['git add -- ' + json.dumps(x, ensure_ascii=False) for x in sorted(set(curated))]
    (OUT / 'suggested_git_add.ps1').write_text('\n'.join(plan) + '\n', encoding='utf-8')
    record('GIT_STAGING_PLAN', 'PASS', f'{len(curated)} curated candidates; see suggested_git_add.ps1 (NOT EXECUTED)')
    private = ('data_raw/', 'data_processed/', 'artifacts/', '.venv', 'logs/')
    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True)
    if tracked.returncode:
        record('PRIVATE_DATA_TRACKED', 'FAIL', 'git ls-files failed')
    else:
        tracked_names = [x.decode('utf-8', errors='replace').replace('\\', '/') for x in tracked.stdout.split(b'\0') if x]
        exposed = [x for x in tracked_names if x.startswith(private) or x.lower().endswith(('.env', '.parquet', '.db', '.sqlite'))]
        record('PRIVATE_DATA_TRACKED', 'FAIL' if exposed else 'PASS', str(exposed[:10]) if exposed else 'No raw/processed data tracked')
    unwanted_markers = ('deliverables/backup/', 'deliverables/rendered_pages/',
                        'scripts/_solo_lgbm_worker.py', 'scripts/patch_export_submission_docx.py',
                        'scripts/export_pdf_com.ps1')
    unwanted = [p for _, p in changed if p.replace('\\', '/').startswith(unwanted_markers) or p in unwanted_markers]
    record('GENERATED_FILES_TO_EXCLUDE', 'WARN' if unwanted else 'PASS',
           f'{len(unwanted)} to omit from staging; example: {unwanted[:5]}')
    large = []
    suspected_secrets = []
    signatures = (r'ghp_[A-Za-z0-9]{25,}', r'github_pat_[A-Za-z0-9_]{25,}',
                  r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9]{25,}', r'AIza[0-9A-Za-z_-]{30,}')
    rx = re.compile('|'.join(signatures))
    for code, name in changed:
        f = ROOT / name
        if not f.is_file():
            continue
        size = f.stat().st_size
        if size >= 50 * 1024 * 1024:
            large.append((name, round(size / (1024 * 1024), 1)))
        if f.suffix.lower() in ('.py', '.ps1', '.json', '.md', '.txt', '.yml', '.yaml', '.toml', '.env') and size < 1024 * 1024:
            try:
                if rx.search(f.read_text(encoding='utf-8', errors='replace')):
                    suspected_secrets.append(name)
            except OSError:
                pass
    record('LARGE_CHANGED_FILES', 'FAIL' if any(s >= 100 for _, s in large) else ('WARN' if large else 'PASS'), str(large[:10]))
    record('POSSIBLE_SECRETS', 'FAIL' if suspected_secrets else 'PASS',
           'Review suspicious files: ' + ', '.join(suspected_secrets) if suspected_secrets else 'No common token prefixes detected in changed text')
    command('git_diff_check', ['git', 'diff', '--check'], 30)
    command('git_staged_diff_check', ['git', 'diff', '--cached', '--check'], 30)
    remote = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, capture_output=True, text=True)
    record('GIT_REMOTE', 'PASS' if remote.returncode == 0 and 'fdic-bank-risk-research' in remote.stdout else 'WARN',
           remote.stdout.strip() if remote.returncode == 0 else 'No origin configured')


def final_report():
    num = {k: sum(x['status'] == k for x in checks) for k in ('PASS', 'WARN', 'FAIL')}
    (OUT / 'audit_results.json').write_text(json.dumps({'created_at': STAMP, 'checks': checks, 'summary': num}, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# FDIC pre-push verification', '', f'Generated: {STAMP}', '',
             f"**PASS {num['PASS']} / WARN {num['WARN']} / FAIL {num['FAIL']}**", '',
             '| Check | Status | Detail |', '|---|---|---|']
    for entry in checks:
        lines.append('| ' + ' | '.join(str(entry[k]).replace('|', '\\|').replace('\n', ' ') for k in ('check', 'status', 'detail')) + ' |')
    lines.extend(['', '## Important', '',
                  '- No model retraining, source ingestion, Git staging, commit, push or Word edits were performed by this audit.',
                  '- Compare corrected CV/OOF claims with the published frozen Test policy before publishing; this audit does not certify a new Test policy.',
                  '- Review `git_changed_files.txt`; stage only curated source/evidence/deliverables, never `git add .` without inspecting.',
                  '- Local SHA-256 versus manifest checks prove local integrity against saved hashes, not remote-source provenance.', ''])
    (OUT / 'PREPUSH_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n=== FINAL SUMMARY ===')
    print(f"PASS={num['PASS']} WARN={num['WARN']} FAIL={num['FAIL']}")
    print('REPORT:', OUT / 'PREPUSH_REPORT.md')
    print('CHANGED FILES:', OUT / 'git_changed_files.txt')
    print('STATUS:', 'BLOCKED - investigate failures' if num['FAIL'] else 'REVIEW WARNINGS BEFORE COMMIT' if num['WARN'] else 'READY FOR MANUAL STAGING')


def main():
    print('=== FDIC PRE-PUSH AUDIT (READ-ONLY FOR MODEL/WORD/TEST) ===')
    record('REPO_ROOT', 'PASS' if (ROOT / '.git').exists() and (ROOT / 'src/fdic_pipeline/model.py').is_file() else 'FAIL', str(ROOT))
    command('pip_check', [sys.executable, '-m', 'pip', 'check'], 120)
    command('project_validation', [sys.executable, 'scripts/validate_entire_project.py', '--check'], 600, 'CURRENT_VALIDATION: PASS')
    audit_quarters()
    audit_documents()
    git_audit()
    final_report()


if __name__ == '__main__':
    main()
