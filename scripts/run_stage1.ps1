# FDIC Stage A. Run from repository root. Does not execute full-data benchmark/model.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath '.\env_setup.ps1')) { throw 'Run from repository root: env_setup.ps1 missing' }
. .\env_setup.ps1
$py = (Resolve-Path -LiteralPath '.\.venv311\Scripts\python.exe').ProviderPath
Write-Host '=== PATCH CHECK (NO FILE EDITS) ===' -ForegroundColor Cyan
& $py .\scripts\stage1_patch.py --check
if ($LASTEXITCODE -ne 0) { throw 'Patch preflight failed: inspect source before applying changes.' }
Write-Host '=== STAGE A PREFLIGHT ===' -ForegroundColor Cyan
& $py .\scripts\stage1_preflight.py
if ($LASTEXITCODE -ne 0) { throw 'Stage A has failed checks; inspect artifacts/diagnostics/stage1_*/preflight.json' }
Write-Host 'STAGE A PASS. Only then proceed to panel and 1x benchmark.' -ForegroundColor Green
