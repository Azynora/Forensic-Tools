$ErrorActionPreference = "Stop"

$workspacePath = Join-Path $PSScriptRoot "forensics-discord.code-workspace"
if (-not (Test-Path -LiteralPath $workspacePath)) {
    throw "Workspace file not found: $workspacePath"
}

$code = Get-Command code -ErrorAction SilentlyContinue
if (-not $code) {
    throw "VS Code CLI 'code' was not found in PATH."
}

Start-Process -FilePath $code.Source -ArgumentList @("-n", "`"$workspacePath`"")

