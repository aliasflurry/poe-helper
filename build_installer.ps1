$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcDir = Join-Path $repoRoot "src"
$installerScript = Join-Path $repoRoot "installer\POE_Helper.iss"

Push-Location $srcDir
try {
    python -m PyInstaller helper.spec --clean --noconfirm
}
finally {
    Pop-Location
}

$innoCompiler = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $innoCompiler) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php, then run this script again."
}

& $innoCompiler $installerScript
