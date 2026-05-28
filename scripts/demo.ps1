# scripts/demo.ps1
# One-command end-to-end demo:
#   1. start the mock server in the background
#   2. run the client to collect 6 ticks
#   3. run the integration pipeline to anonymize them
#   4. print the resulting file path
#
# Run from the repo root: powershell -File scripts\demo.ps1
$ErrorActionPreference = "Stop"

$repoRoot   = Resolve-Path (Join-Path $PSScriptRoot "..")
$serverDir  = Join-Path $repoRoot "mock\server"
$clientDir  = Join-Path $repoRoot "mock\client-dashboard"
$pipelineDir = Join-Path $repoRoot "integration\pipeline"
$outDir     = Join-Path $repoRoot "integration\out"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$rawJson  = Join-Path $outDir "ticks.raw.json"
$anonJson = Join-Path $outDir "ticks.anon.json"

# Resolve a server venv python (assumes scripts\run_mock.ps1 already created it).
$serverPy = Join-Path $serverDir ".venv\Scripts\python.exe"
if (-not (Test-Path $serverPy)) {
    Push-Location $serverDir
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Pop-Location
}
$clientPy = Join-Path $clientDir ".venv\Scripts\python.exe"
if (-not (Test-Path $clientPy)) {
    Push-Location $clientDir
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Pop-Location
}

Write-Host "[1/3] Launching mock server in the background ..."
$server = Start-Process -FilePath $serverPy `
    -ArgumentList "app.py" `
    -WorkingDirectory $serverDir `
    -PassThru `
    -WindowStyle Hidden

try {
    # INTENTIONAL BUG: no readiness wait. The client races the Flask
    # boot and can hit ConnectionRefused on a cold machine.
    Write-Host "[2/3] Collecting 6 ticks via the client ..."
    & $clientPy (Join-Path $clientDir "client.py") `
        --server "http://127.0.0.1:5050" `
        --tickers "ACME,GLOBEX,INITECH" `
        --buffer 6 `
        --out $rawJson `
        --format json

    Write-Host "[3/3] Running integration pipeline ..."
    & $clientPy (Join-Path $pipelineDir "run_pipeline.py") `
        --input $rawJson `
        --out-dir $outDir

    Write-Host ""
    Write-Host "Demo complete."
    Write-Host "  Raw ticks      : $rawJson"
    Write-Host "  Anonymized out : $anonJson"
}
finally {
    if ($server -and -not $server.HasExited) {
        Write-Host "Stopping mock server (PID $($server.Id)) ..."
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
}
