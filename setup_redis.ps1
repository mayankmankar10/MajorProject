# Redis Setup Script for SmartServe (PowerShell)

Write-Host "🚀 Setting up Redis for SmartServe..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    New-Item -Path ".env" -ItemType File -Force | Out-Null
}

# Function to update or add env variable
function Update-EnvVariable {
    param(
        [string]$Key,
        [string]$Value
    )
    
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    $found = $false
    $newContent = @()
    
    foreach ($line in $envContent) {
        if ($line -match "^$Key=") {
            $newContent += "$Key=$Value"
            $found = $true
        } else {
            $newContent += $line
        }
    }
    
    if (-not $found) {
        $newContent += "$Key=$Value"
    }
    
    $newContent | Set-Content ".env"
}

Write-Host "📝 Updating .env configuration..." -ForegroundColor Yellow

# Set Redis configuration
Update-EnvVariable "REDIS_ENABLED" "true"
Update-EnvVariable "REDIS_URL" "redis://localhost:6379"
Update-EnvVariable "CHAT_SESSION_TTL" "3600"

Write-Host ""
Write-Host "✅ Redis configuration updated in .env" -ForegroundColor Green
Write-Host ""
Write-Host "🔄 Please restart your backend server to apply changes:" -ForegroundColor Cyan
Write-Host "   uvicorn backend.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
