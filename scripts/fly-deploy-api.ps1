# One-shot: verify Fly login, push secrets from .env, deploy API (Dockerfile + fly.toml).
# Run from repo root: npm run fly:deploy   OR   powershell -File scripts/fly-deploy-api.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FlyExe = Join-Path $env:USERPROFILE ".fly\bin\flyctl.exe"
$FlyToml = Join-Path $Root "fly.toml"

if (-not (Test-Path $FlyExe)) {
    Write-Error "flyctl not found. Install: powershell -Command `"iwr https://fly.io/install.ps1 -useb | iex`" then restart the terminal."
}

Push-Location $Root
try {
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $null = & $FlyExe auth whoami 2>&1
    $loggedIn = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevEap
    if (-not $loggedIn) {
        Write-Host "Not logged in to Fly.io. Run this in a terminal (browser will open):"
        Write-Host "  & `"$FlyExe`" auth login"
        exit 1
    }

    Write-Host "Importing secrets from .env ..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "fly-push-secrets.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Deploying API ..."
    & $FlyExe deploy -c $FlyToml
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Done. Set Vercel VITE_API_BASE_URL to https://<app>.fly.dev (see fly.toml app name) and redeploy the frontend."
}
finally {
    Pop-Location
}
