# scripts/run_tests.ps1
# Install test deps in a venv under integration/tests/ and run pytest.
# Run from the repo root: powershell -File scripts\run_tests.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$testsDir = Join-Path $repoRoot "integration\tests"

Push-Location $testsDir
try {
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        & .\.venv\Scripts\python.exe -m pip install --upgrade pip > $null
        & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    }
    & .\.venv\Scripts\python.exe -m pytest -v
}
finally {
    Pop-Location
}
