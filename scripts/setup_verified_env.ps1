# Run from the repository root: . .\scripts\setup_verified_env.ps1
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).ProviderPath
$py = Join-Path $repo '.venv311\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $py)) {
    throw 'Missing .venv311 Python'
}

$env:PYSPARK_PYTHON = $py
$env:PYSPARK_DRIVER_PYTHON = $py
$env:PYTHONPATH = Join-Path $repo 'src'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:SPARK_LOCAL_IP = '127.0.0.1'
$env:SPARK_LOCAL_HOSTNAME = 'localhost'

if (-not $env:SPARK_HOME) {
    $env:SPARK_HOME = 'F:\pyspark_home'
}
if (-not $env:HADOOP_HOME) {
    $env:HADOOP_HOME = 'F:\hadoop_home'
}

Write-Host 'Spark Python worker:' $py
