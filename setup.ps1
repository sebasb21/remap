# One-shot setup for Windows. Run from PowerShell in this folder:
#   .\setup.ps1
$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher 'py' not found. Install Python 3.10+ from https://www.python.org/downloads/windows/ and re-run."
}

if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment in .venv ..."
    py -m venv .venv
}

Write-Host "Installing dependencies ..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Done. To run:"
Write-Host "  .\run.ps1"
Write-Host ""
Write-Host "If the virtual gamepad fails to start, install ViGEmBus:"
Write-Host "  https://github.com/nefarius/ViGEmBus/releases"
