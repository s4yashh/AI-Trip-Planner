param([ValidateSet("backend", "frontend")][string]$Service = "backend")
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if ($Service -eq "backend") {
    if (-not (Test-Path -LiteralPath ".venv/Scripts/python.exe")) {
        throw "Install application dependencies first; see README.md."
    }
    & ./.venv/Scripts/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
} else {
    Set-Location -LiteralPath (Join-Path $PSScriptRoot "frontend")
    & npm.cmd run dev -- --hostname 127.0.0.1
}
