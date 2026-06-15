<#
  H5 validation (Windows) — verify a BUILT, SIGNED Secure Vault installer + bundled binaries.

  Does NOT sign anything; only checks an Authenticode signature is present and valid (so
  SmartScreen/Defender won't block the installer and the bundled age.exe runs). Run on a Windows
  machine with the Windows SDK (signtool) after `cargo tauri build` + signing.

  Usage:
    powershell -ExecutionPolicy Bypass -File scripts\validate-windows-signing.ps1 `
        -Installer "path\to\Secure Vault_x.y.z_x64-setup.exe" `
        -AgeBinaries @("path\to\age.exe","path\to\age-keygen.exe")

  Exit 0 = PASS. Non-zero = FAIL (do NOT ship / do NOT start beta).
#>
param(
  [Parameter(Mandatory = $true)][string]$Installer,
  [string[]]$AgeBinaries = @()
)

$ErrorActionPreference = "Continue"
$fail = $false
function Pass($m) { Write-Host "  PASS  $m" }
function Bad($m)  { Write-Host "  FAIL  $m"; $script:fail = $true }

# Locate signtool (Windows SDK).
$signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if (-not $signtool) {
  $cand = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
          Where-Object { $_.FullName -match "x64" } | Select-Object -First 1
  if ($cand) { $signtool = $cand.FullName } else { Write-Error "signtool.exe not found (install the Windows SDK)"; exit 2 }
} else { $signtool = $signtool.Source }

function Verify-Sig($path, $label) {
  if (-not (Test-Path $path)) { Bad "$label not found: $path"; return }
  # /pa = use the Authenticode policy; /v = verbose. Also require a timestamp.
  $out = & $signtool verify /pa /v $path 2>&1
  if ($LASTEXITCODE -eq 0) {
    if ($out -match "Timestamp") { Pass "$label signed + timestamped" }
    else { Bad "$label signed but NOT timestamped (signature expires with the cert)" }
  } else {
    Bad "$label signature invalid/absent — $($out -join ' ')"
  }
}

Write-Host "== H5 Windows signing validation =="
Write-Host "signtool: $signtool"
Write-Host "installer: $Installer"

Verify-Sig $Installer "installer"

# The bundled age toolchain must ALSO be signed (it ships inside the installer payload and runs as
# a subprocess; an unsigned/SmartScreen-flagged age.exe breaks crypto on locked-down machines).
if ($AgeBinaries.Count -eq 0) {
  Bad "no -AgeBinaries provided; the bundled age.exe / age-keygen.exe must be verified too"
} else {
  foreach ($b in $AgeBinaries) { Verify-Sig $b "bundled $(Split-Path $b -Leaf)" }
}

Write-Host ""
if (-not $fail) {
  Write-Host "RESULT: PASS — installer and bundled binaries are validly signed."
  Write-Host "Recommended final manual check: on a CLEAN Windows 10 + Windows 11 VM, run the installer, launch, create a vault + add a file (confirms no SmartScreen/Defender block of age.exe)."
  exit 0
} else {
  Write-Host "RESULT: FAIL — H5 not satisfied. Do NOT distribute or start beta."
  exit 1
}
