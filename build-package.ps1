$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$buildTempRoot = Join-Path $root ".build-temp"
New-Item -ItemType Directory -Force -Path $buildTempRoot | Out-Null
$env:TEMP = $buildTempRoot
$env:TMP = $buildTempRoot
$buildVenvPython = Join-Path $root ".build-venv\Scripts\python.exe"
$pythonOverride = $env:FDCTL_BUILD_PYTHON
if ($pythonOverride) {
    $python = $pythonOverride
}
elseif (Test-Path -LiteralPath $buildVenvPython) {
    & $buildVenvPython -V | Out-Null
    $versionExitCode = $LASTEXITCODE
    & $buildVenvPython -m pip --version | Out-Null
    if ($versionExitCode -eq 0 -and $LASTEXITCODE -eq 0) {
        $python = $buildVenvPython
    }
    else {
        $buildVenvRoot = Join-Path $root ".build-venv"
        if ((Resolve-Path -LiteralPath $buildVenvRoot).Path -ne $buildVenvRoot) {
            throw "Unexpected build environment path: $buildVenvRoot"
        }
        Remove-Item -LiteralPath $buildVenvRoot -Recurse -Force
        $python = "python"
        & $python -m venv $buildVenvRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to recreate the build virtual environment with $python."
        }
        $python = $buildVenvPython
    }
}
else {
    $python = "python"
    & $python -m venv (Join-Path $root ".build-venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the build virtual environment with $python."
    }
    $python = $buildVenvPython
}
& $python -V | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Python executable is unavailable: $python"
}

$bundleRoot = Join-Path $root "dist\ForensicsSuite"
$bundleRuntimeRoot = Join-Path $bundleRoot "fdctl_runtime"
$publicRoot = Join-Path $root "dist\github-release"
$buildRoot = Join-Path $root "build\pyinstaller"
$buildSession = "session-" + [guid]::NewGuid().ToString("N")
$workRoot = Join-Path $buildRoot $buildSession
$distRoot = Join-Path $workRoot "release-dist"
$guiDistRoot = Join-Path $workRoot "gui-dist"
$specRoot = Join-Path $workRoot "specs"
$pyInstallerWorkRoot = Join-Path $workRoot "fdctl-cli"
$guiPyInstallerWorkRoot = Join-Path $workRoot "fdctl-gui"
$releaseZip = Join-Path $root "dist\ForensicsSuite_portable.zip"
$docsToCopy = @(
    "README.md",
    "README.vi.md",
    "README.en.md",
    "USAGE_GUIDE.md",
    "COPYRIGHT_NOTICE.md",
    "LICENSE_PROPRIETARY.md",
    "EULA.md",
    "CHANGELOG_version.md"
)
$scriptsToCopy = @(
    "fdctl.cmd",
    "fdctl.ps1",
    "launch-analysis-terminal.cmd",
    "activate-license.cmd"
)

foreach ($path in @($bundleRoot, $publicRoot)) {
    if (Test-Path -LiteralPath $path) {
        try {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
        catch {
            Get-ChildItem -LiteralPath $path -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
if (Test-Path -LiteralPath $releaseZip) {
    Remove-Item -LiteralPath $releaseZip -Force
}

New-Item -ItemType Directory -Force -Path $bundleRoot, $bundleRuntimeRoot, $publicRoot, $buildRoot, $workRoot, $distRoot, $guiDistRoot, $specRoot, $pyInstallerWorkRoot, $guiPyInstallerWorkRoot | Out-Null

Get-ChildItem -Recurse -Directory -Path $backend -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -File -Path $backend -Include *.pyc, *.pyo -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Path (Join-Path $backend "src") -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Push-Location $root
& $python -m pip install -r (Join-Path $root "requirements-build.txt")
$installExitCode = $LASTEXITCODE
Pop-Location
if ($installExitCode -ne 0) {
    throw "Failed to install build requirements with $python."
}

Push-Location $backend
& $python -m PyInstaller --noconfirm --clean --onedir --console --name fdctl_runtime --distpath $distRoot --workpath $pyInstallerWorkRoot --specpath $specRoot --paths "$backend\src" "$backend\src\fdctl\cli_entry.py"
$buildExitCode = $LASTEXITCODE
if ($buildExitCode -eq 0) {
    & $python -m PyInstaller --noconfirm --clean --onedir --windowed --name ForensicsSuite --distpath $guiDistRoot --workpath $guiPyInstallerWorkRoot --specpath $specRoot --paths "$backend\src" "$backend\src\fdctl\__main__.py"
    $buildExitCode = $LASTEXITCODE
}
Pop-Location
if ($buildExitCode -ne 0) {
    throw "PyInstaller failed with exit code $buildExitCode."
}

$runtimeSourceRoot = Join-Path $distRoot "fdctl_runtime"
$runtimeExeSource = Join-Path $runtimeSourceRoot "fdctl_runtime.exe"
$runtimeInternalSource = Join-Path $runtimeSourceRoot "_internal"
$guiRuntimeRoot = Join-Path $guiDistRoot "ForensicsSuite"
$guiExeSource = Join-Path $guiRuntimeRoot "ForensicsSuite.exe"
$guiInternalSource = Join-Path $guiRuntimeRoot "_internal"
$bundleInternalRoot = Join-Path $bundleRuntimeRoot "_internal"

if (-not (Test-Path -LiteralPath $runtimeExeSource)) {
    throw "Missing built runtime executable: $runtimeExeSource"
}
if (-not (Test-Path -LiteralPath $runtimeInternalSource)) {
    throw "Missing built runtime internal folder: $runtimeInternalSource"
}
if (-not (Test-Path -LiteralPath $guiExeSource)) {
    throw "Missing built GUI executable: $guiExeSource"
}
if (-not (Test-Path -LiteralPath $guiInternalSource)) {
    throw "Missing GUI runtime dependencies: $guiInternalSource"
}

Copy-Item -LiteralPath $runtimeExeSource -Destination (Join-Path $bundleRuntimeRoot "fdctl_runtime.exe") -Force
Copy-Item -LiteralPath $guiExeSource -Destination (Join-Path $bundleRuntimeRoot "ForensicsSuite.exe") -Force
New-Item -ItemType Directory -Force -Path $bundleInternalRoot | Out-Null
Copy-Item -Path (Join-Path $runtimeInternalSource "*") -Destination $bundleInternalRoot -Recurse -Force
Copy-Item -Path (Join-Path $guiInternalSource "*") -Destination $bundleInternalRoot -Recurse -Force

$bundleRuntimeExe = Join-Path $bundleRuntimeRoot "fdctl_runtime.exe"
if (-not (Test-Path -LiteralPath $bundleRuntimeExe)) {
    & cmd /c copy /y "`"$runtimeExeSource`"" "`"$bundleRuntimeExe`"" | Out-Null
}
if (-not (Test-Path -LiteralPath $bundleRuntimeExe)) {
    throw "Failed to copy runtime executable into bundle: $bundleRuntimeExe"
}

$bundlePythonDll = Get-ChildItem -LiteralPath $bundleInternalRoot -File -Filter "python3*.dll" | Select-Object -First 1
if (-not $bundlePythonDll) {
    throw "Failed to copy a bundled Python runtime DLL into $bundleInternalRoot"
}

Get-ChildItem -LiteralPath $bundleRuntimeRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $bundleRuntimeRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @(".py", ".pyi", ".ts", ".tsx", ".spec", ".toml") } | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $bundleRuntimeRoot -Recurse -File -Filter "direct_url.json" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $bundleRuntimeRoot -Recurse -Directory -Filter "*.dist-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
$runtimeSourceFiles = Get-ChildItem -LiteralPath $bundleRuntimeRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @(".py", ".pyi", ".ts", ".tsx", ".spec", ".toml") }
if ($runtimeSourceFiles.Count -gt 0) {
    $badFiles = ($runtimeSourceFiles | ForEach-Object { $_.FullName.Substring($bundleRuntimeRoot.Length).TrimStart("\") }) -join ", "
    throw "Public runtime still contains source files: $badFiles"
}

foreach ($script in $scriptsToCopy) {
    Copy-Item -LiteralPath (Join-Path $root $script) -Destination (Join-Path $bundleRoot $script) -Force
}
foreach ($doc in $docsToCopy) {
    Copy-Item -LiteralPath (Join-Path $root $doc) -Destination (Join-Path $bundleRoot $doc) -Force
}

$version = & $python -c "import pathlib, sys; sys.path.insert(0, sys.argv[1]); from fdctl import __release__; print(__release__)" (Join-Path $backend "src")
$version = ($version | Select-Object -Last 1).ToString().Trim()
$bundleFiles = @()
Get-ChildItem -LiteralPath $bundleRoot -Recurse -File | Where-Object { $_.Name -notin @("BUILD_PROVENANCE.json", "SHA256SUMS.txt") } | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    $relativePath = $_.FullName.Substring($bundleRoot.Length).TrimStart("\")
    $bundleFiles += [ordered]@{
        path      = $relativePath
        sha256    = $hash.Hash.ToLowerInvariant()
        sizeBytes = $_.Length
    }
}

$bundleProvenance = [ordered]@{
    project               = "Forensics Suite"
    owner                 = [ordered]@{
        name  = "Truong Trieu Vy"
        email = "trieuvy9198@gmail.com"
    }
    generatedAtUtc        = (Get-Date).ToUniversalTime().ToString("o")
    distributionMode      = "windows-gui-installer-and-source-cli"
    bundleVersion         = $version
    runtimeEntryPoint     = "fdctl_runtime\fdctl_runtime.exe"
    licenseRequired       = $true
    builtInTrial          = [ordered]@{
        durationDays = 7
        seats        = 1
        activation   = "local seven-day demo trial; owner-issued device-bound Ed25519 keys"
        storage      = "%LOCALAPPDATA%\FORENSICS_DISCORD\license"
    }
    supportedLicenseTypes = @(
        "issued_7d",
        "issued_30d",
        "issued_365d"
    )
    defaultWorkspaceRoot  = "%USERPROFILE%\Documents\Forensics Suite"
    files                 = $bundleFiles
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$signatureInputPath = Join-Path $workRoot "bundle-provenance.tmp.json"
[System.IO.File]::WriteAllText($signatureInputPath, ($bundleProvenance | ConvertTo-Json -Depth 6), $utf8NoBom)
$signature = & $python -c "import json, pathlib, sys; sys.path.insert(0, sys.argv[2]); from fdctl.services.license_service import integrity_signature_for_manifest; data=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')); print(integrity_signature_for_manifest(data))" $signatureInputPath (Join-Path $backend "src")
$bundleProvenance["integritySignature"] = ($signature | Select-Object -Last 1).ToString().Trim()
$bundleProvenancePath = Join-Path $bundleRoot "BUILD_PROVENANCE.json"
[System.IO.File]::WriteAllText($bundleProvenancePath, ($bundleProvenance | ConvertTo-Json -Depth 6), $utf8NoBom)

$bundleHashes = @()
Get-ChildItem -LiteralPath $bundleRoot -Recurse -File | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    $relativePath = $_.FullName.Substring($bundleRoot.Length).TrimStart("\")
    $bundleHashes += ("{0} *{1}" -f $hash.Hash.ToLowerInvariant(), $relativePath)
}
[System.IO.File]::WriteAllLines((Join-Path $bundleRoot "SHA256SUMS.txt"), $bundleHashes, $utf8NoBom)

Copy-Item -Path (Join-Path $bundleRoot "*") -Destination $publicRoot -Recurse -Force

$zipStageRoot = Join-Path $workRoot "zip-stage"
$zipCreated = $false
for ($attempt = 1; $attempt -le 5 -and -not $zipCreated; $attempt++) {
    try {
        if (Test-Path -LiteralPath $zipStageRoot) {
            Remove-Item -LiteralPath $zipStageRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
        New-Item -ItemType Directory -Force -Path $zipStageRoot | Out-Null
        Copy-Item -Path (Join-Path $bundleRoot "*") -Destination $zipStageRoot -Recurse -Force
        Compress-Archive -Path (Join-Path $zipStageRoot "*") -DestinationPath $releaseZip -CompressionLevel Optimal -Force
        $zipCreated = $true
    }
    catch {
        if ($attempt -ge 5) {
            throw
        }
        Start-Sleep -Seconds 2
    }
}

if (-not $zipCreated -or -not (Test-Path -LiteralPath $releaseZip)) {
    throw "Failed to create the portable release archive: $releaseZip"
}

$zipItem = Get-Item -LiteralPath $releaseZip
if ($zipItem.Length -le 0) {
    throw "The portable release archive is empty: $releaseZip"
}

Write-Host "Portable bundle created: $releaseZip ($($zipItem.Length) bytes)"
Write-Host "Expanded bundle created: $publicRoot"

$isccCandidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
if ($isccCandidates) {
    $iscc = $isccCandidates | Select-Object -First 1
    $installerScript = Join-Path $root "installer\ForensicsSuite.iss"
    & $iscc "/DBundleDir=$bundleRoot" "/DOutputDir=$publicRoot" $installerScript
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE." }
    Write-Host "Setup installer created: $(Join-Path $publicRoot 'ForensicsSuite_Setup.exe')"
}
else {
    Write-Warning "Inno Setup 6 was not found. Portable ZIP is ready; install Inno Setup 6 to create Setup.exe."
}

$releaseArtifactPaths = @($releaseZip)
$setupArtifact = Join-Path $publicRoot "ForensicsSuite_Setup.exe"
if (Test-Path -LiteralPath $setupArtifact) { $releaseArtifactPaths += $setupArtifact }
$releaseChecksums = foreach ($artifact in $releaseArtifactPaths) {
    $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0} *{1}" -f $hash, (Split-Path -Leaf $artifact)
}
[System.IO.File]::WriteAllLines((Join-Path $publicRoot "RELEASE_SHA256SUMS.txt"), $releaseChecksums, $utf8NoBom)
Write-Host "Release artifact checksums written: $(Join-Path $publicRoot 'RELEASE_SHA256SUMS.txt')"
