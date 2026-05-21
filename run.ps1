# Launch remap using the project venv. Pass 'identify' to enter identify mode:
#   .\run.ps1 identify
$ErrorActionPreference = "Stop"

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    Write-Error "No .venv found. Run .\setup.ps1 first."
}

& .\.venv\Scripts\python.exe main.py @args
