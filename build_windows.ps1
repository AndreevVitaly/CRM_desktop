$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = "python"
$distDir = Join-Path $root "dist\PULSAR"
$internalDb = Join-Path $distDir "_internal\medcrm.db"

if (Test-Path $distDir) {
  Remove-Item -LiteralPath $distDir -Recurse -Force
}

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name PULSAR `
  --add-data "assets;assets" `
  main.py

Copy-Item -LiteralPath (Join-Path $root "medcrm.db") -Destination (Join-Path $distDir "medcrm.db") -Force
if (Test-Path $internalDb) {
  Remove-Item -LiteralPath $internalDb -Force
}

Write-Host ""
Write-Host "Build complete: $root\dist\PULSAR"
