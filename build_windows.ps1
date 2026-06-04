param(
  [switch]$IncludeDatabase,
  [switch]$Installer
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = "python"
$distDir = Join-Path $root "dist\PULSAR"
$internalDb = Join-Path $distDir "_internal\medcrm.db"
$installerScript = Join-Path $root "installer\PULSAR.iss"
$installerOutput = Join-Path $root "dist\installer\PULSAR_Setup.exe"

function Find-InnoCompiler {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  $fromPath = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
  if ($fromPath) {
    return $fromPath.Source
  }

  return $null
}

if (Test-Path $distDir) {
  Remove-Item -LiteralPath $distDir -Recurse -Force
}

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  PULSAR.spec

if ($IncludeDatabase) {
  Copy-Item -LiteralPath (Join-Path $root "medcrm.db") -Destination (Join-Path $distDir "medcrm.db") -Force
  if (Test-Path $internalDb) {
    Remove-Item -LiteralPath $internalDb -Force
  }
}

Write-Host ""
Write-Host "Build complete: $root\dist\PULSAR"

if ($Installer) {
  $iscc = Find-InnoCompiler
  if (-not $iscc) {
    throw "Inno Setup не найден. Установите Inno Setup 6 и повторите: .\build_windows.ps1 -Installer"
  }
  if (-not (Test-Path $installerScript)) {
    throw "Не найден сценарий установщика: $installerScript"
  }

  & $iscc $installerScript
  Write-Host "Installer complete: $installerOutput"
}
