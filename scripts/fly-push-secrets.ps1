# Push selected keys from repo-root .env to Fly (stdin import). Does not print secret values.
# Requires: flyctl installed, `flyctl auth login` done, app in fly.toml exists or will be created on first deploy.

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EnvFile = Join-Path $Root ".env"
$FlyExe = Join-Path $env:USERPROFILE ".fly\bin\flyctl.exe"
$FlyToml = Join-Path $Root "fly.toml"

if (-not (Test-Path $FlyExe)) {
    Write-Error "flyctl not found. Install: powershell -Command `"iwr https://fly.io/install.ps1 -useb | iex`""
}

if (-not (Test-Path $EnvFile)) {
    Write-Error "Missing .env at $EnvFile (copy from .env.example and add keys)."
}

if (-not (Test-Path $FlyToml)) {
    Write-Error "Missing fly.toml at $FlyToml"
}

$allowed = @(
    "GEMINI_API_KEY",
    "NEWSDATA_API_KEY",
    "CORS_ORIGINS",
    "ENVIRONMENT",
    "SKIP_GEMINI_SENTIMENT",
    "ANALYSIS_CACHE_TTL",
    "GEMINI_MODEL",
    "PERPLEXITY_API_KEY"
)

$out = New-Object System.Collections.Generic.List[string]
foreach ($line in Get-Content $EnvFile -Encoding UTF8) {
    $t = $line.Trim()
    if ($t.StartsWith("#") -or [string]::IsNullOrWhiteSpace($t)) { continue }
    $eq = $t.IndexOf("=")
    if ($eq -lt 1) { continue }
    $key = $t.Substring(0, $eq).Trim()
    if ($allowed -notcontains $key) { continue }
    $val = $t.Substring($eq + 1).Trim()
    if ($val.Length -ge 2 -and $val.StartsWith('"') -and $val.EndsWith('"')) {
        $val = $val.Substring(1, $val.Length - 2)
    }
    if ($val.Length -ge 2 -and $val.StartsWith("'") -and $val.EndsWith("'")) {
        $val = $val.Substring(1, $val.Length - 2)
    }
    if ([string]::IsNullOrWhiteSpace($val)) { continue }
    $out.Add("${key}=${val}")
}

if ($out.Count -eq 0) {
    Write-Warning "No allowed non-empty keys found in .env (see allowlist in this script)."
    exit 0
}

$hasGemini = $out | Where-Object { $_ -like "GEMINI_API_KEY=*" }
$hasNews = $out | Where-Object { $_ -like "NEWSDATA_API_KEY=*" }
if (-not $hasGemini -or -not $hasNews) {
    Write-Warning "GEMINI_API_KEY and NEWSDATA_API_KEY should both be set in .env for /analyze to work."
}

$hasCors = $out | Where-Object { $_ -like "CORS_ORIGINS=*" }
if (-not $hasCors) {
    Write-Warning "CORS_ORIGINS not in .env — add your Vercel URL, e.g. CORS_ORIGINS=https://stockmarket-rho.vercel.app"
}

$tmp = [System.IO.Path]::GetTempFileName()
try {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmp, ($out -join "`n") + "`n", $utf8)
    Get-Content -Path $tmp -Raw -Encoding UTF8 | & $FlyExe secrets import -c $FlyToml
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Fly secrets updated for app in fly.toml."
}
finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
