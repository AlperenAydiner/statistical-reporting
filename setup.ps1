# statrep setup for Windows — provisions an isolated virtual environment
# and probes optional capabilities (R, LibreOffice). Never touches system
# Python.
#
# Usage:
#   .\setup.ps1            install everything
#   .\setup.ps1 -Check     re-run only the capability probe (= `statrep doctor`)

param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvDir = Join-Path $ScriptDir ".venv"
$CapDir = Join-Path $ScriptDir ".statrep"
$CapFile = Join-Path $CapDir "capabilities.json"

function Find-Python {
    foreach ($cand in @("python3.12", "python3.11", "python3.10", "python", "py")) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $ver = & $cmd.Source -c "import sys; print('%d.%d' % sys.version_info[:2])"
                $parts = $ver.Split(".")
                if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) {
                    return $cmd.Source
                }
            } catch {}
        }
    }
    return $null
}

if (-not $Check) {
    Write-Host "[1/4] Python" -ForegroundColor Cyan
    $PythonBin = Find-Python
    if (-not $PythonBin) {
        Write-Host "No Python >= 3.10 found. Install Python 3.10+ from python.org and re-run." -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: $PythonBin"

    Write-Host "[2/4] Virtual environment" -ForegroundColor Cyan
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        Write-Host "  Using uv (fast path)"
        & uv venv --python $PythonBin $VenvDir | Out-Null
        $VenvPy = Join-Path $VenvDir "Scripts\python.exe"
        $env:VIRTUAL_ENV = $VenvDir
        & uv pip install --python $VenvPy -r requirements.txt
        & uv pip install --python $VenvPy -e .
    } else {
        & $PythonBin -m venv $VenvDir
        $VenvPy = Join-Path $VenvDir "Scripts\python.exe"
        & $VenvPy -m pip install -q --upgrade pip
        & $VenvPy -m pip install -q -r requirements.txt
        & $VenvPy -m pip install -q -e .
    }
    Write-Host "  OK: installed into $VenvDir"
    Write-Host "[3/4] Capability probe" -ForegroundColor Cyan
} else {
    $VenvPy = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Path $VenvPy)) {
        Write-Host "No .venv found — run .\setup.ps1 first (without -Check)." -ForegroundColor Red
        exit 1
    }
    Write-Host "Capability probe" -ForegroundColor Cyan
}

New-Item -ItemType Directory -Force -Path $CapDir | Out-Null

$RPresent = $false
$RPackages = "[]"
$rscript = Get-Command Rscript -ErrorAction SilentlyContinue
if ($rscript) {
    $RPresent = $true
    try {
        $RPackages = & Rscript -e 'cat(paste0("[", paste(shQuote(rownames(installed.packages()), type="cmd"), collapse=","), "]"))' 2>$null
    } catch { $RPackages = "[]" }
    Write-Host "  OK: R found"
} else {
    Write-Host "  R not found - SEM/HLM analyses and the flextable table path will be unavailable (optional)" -ForegroundColor Yellow
}

$SofficePresent = $false
$SofficeWorks = $false
$soffice = Get-Command soffice -ErrorAction SilentlyContinue
if (-not $soffice) {
    $defaultPath = "C:\Program Files\LibreOffice\program\soffice.exe"
    if (Test-Path $defaultPath) { $soffice = Get-Item $defaultPath }
}
if ($soffice) {
    $SofficePresent = $true
    $ProbeDir = Join-Path $env:TEMP "statrep-probe-$(Get-Random)"
    New-Item -ItemType Directory -Force -Path $ProbeDir | Out-Null
    "probe" | Out-File -FilePath (Join-Path $ProbeDir "probe.txt") -Encoding utf8
    $OutDir = Join-Path $ProbeDir "out"
    try {
        $proc = Start-Process -FilePath $soffice.Source -ArgumentList @(
            "--headless", "-env:UserInstallation=file:///$($ProbeDir -replace '\\','/')/profile",
            "--convert-to", "pdf", "--outdir", $OutDir, (Join-Path $ProbeDir "probe.txt")
        ) -Wait -PassThru -NoNewWindow -Timeout 25
        if (Test-Path (Join-Path $OutDir "probe.pdf")) {
            $SofficeWorks = $true
            Write-Host "  OK: LibreOffice found and conversion works"
        } else {
            Write-Host "  LibreOffice binary found but conversion failed - PDF export and page-count measurement will be skipped" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  LibreOffice binary found but conversion failed - PDF export and page-count measurement will be skipped" -ForegroundColor Yellow
    }
    Remove-Item -Recurse -Force $ProbeDir -ErrorAction SilentlyContinue
} else {
    Write-Host "  LibreOffice not found - PDF export and page-count measurement will be skipped (optional)" -ForegroundColor Yellow
}

$capJson = @{
    r_present       = $RPresent
    r_packages      = ($RPackages | ConvertFrom-Json -ErrorAction SilentlyContinue)
    soffice_present = $SofficePresent
    soffice_works   = $SofficeWorks
} | ConvertTo-Json -Depth 5
$capJson | Out-File -FilePath $CapFile -Encoding utf8
Write-Host "  Wrote $CapFile"

if (-not $Check) {
    Write-Host "[4/4] Done" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "statrep is installed. Activate it with:" -ForegroundColor Green
    Write-Host "  .venv\Scripts\Activate.ps1"
    Write-Host "Or run directly:"
    Write-Host "  .venv\Scripts\statrep.exe doctor"
    Write-Host "  .venv\Scripts\statrep.exe build --input your-data.xlsx --tier standard --lang tr"
}
