# scripts/run_mock.ps1
# Bring up the mock SSE server on http://127.0.0.1:5050.
# Run from the repo root: powershell -File scripts\run_mock.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$serverDir = Join-Path $repoRoot "mock\server"

Push-Location $serverDir
try {
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        & .\.venv\Scripts\python.exe -m pip install --upgrade pip > $null
        & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    }
    Write-Host "Starting mock server on http://127.0.0.1:5050 ..."
    & .\.venv\Scripts\python.exe app.py
}
finally {
    Pop-Location
}
