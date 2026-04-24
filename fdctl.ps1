$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backendSrc = Join-Path $root "backend\src"
$bundledExeCandidates = @(
    (Join-Path $root "fdctl_runtime\fdctl_runtime.exe"),
    (Join-Path $root "dist\FORENSICS_DISCORD\fdctl_runtime\fdctl_runtime.exe"),
    (Join-Path $root "build\pyinstaller\release-dist\fdctl_runtime\fdctl_runtime.exe")
)
$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
$codexRuntimePython = "C:\Users\Developer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

if ($args.Count -gt 0 -and $args[0] -eq "menu") {
    try {
        $Host.UI.RawUI.WindowTitle = "FORENSICS_DISCORD Investigator"
    } catch {
    }
}

if (Test-Path -LiteralPath $backendSrc) {
    $env:PYTHONPATH = if ($env:PYTHONPATH) { "$backendSrc;$env:PYTHONPATH" } else { $backendSrc }
}

$bundledExe = $bundledExeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$pythonSourceReady = $false
if (Test-Path -LiteralPath $pythonExe) {
    try {
        & $pythonExe -V | Out-Null
        $pythonSourceReady = $true
    } catch {
        $pythonSourceReady = $false
    }
}
if ($bundledExe) {
    & $bundledExe @args
    if ($args.Count -gt 0 -and $args[0] -eq "menu") {
        exit 0
    }
} elseif ($pythonSourceReady) {
    & $pythonExe -m fdctl @args
} elseif (Test-Path -LiteralPath $codexRuntimePython) {
    & $codexRuntimePython -m fdctl @args
} else {
    python -m fdctl @args
}

if ($args.Count -gt 0 -and $args[0] -eq "menu") {
    exit 0
}
