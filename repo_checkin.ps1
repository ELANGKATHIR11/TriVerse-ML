# repo_checkin.ps1
$LogFile = Join-Path -Path $PSScriptRoot -ChildPath "repo_checkin.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Log-Message {
    param([string]$message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $formatted = "[$ts] $message"
    Write-Output $formatted
    Add-Content -Path $LogFile -Value $formatted
}

Log-Message "Starting repository check-in process..."

# 1. Check Git Status
Log-Message "Checking Git Status..."
$gitStatus = git status --porcelain
if ($gitStatus) {
    Log-Message "Found local changes/untracked files:"
    Log-Message $gitStatus
} else {
    Log-Message "No local changes detected."
}

# 2. Run Backend Tests
Log-Message "Running backend tests..."
$backendDir = Join-Path -Path $PSScriptRoot -ChildPath "backend\unified_api"
Push-Location $backendDir
try {
    # Run pytest inside the conda environment
    $testResult = conda run -n dgpu-aiml pytest tests 2>&1
    Log-Message "Test Output:"
    Log-Message ($testResult -join "`n")
    if ($LASTEXITCODE -ne 0) {
        Log-Message "WARNING: Backend tests failed!"
    } else {
        Log-Message "SUCCESS: All backend tests passed."
    }
} catch {
    Log-Message "ERROR: Failed to run backend tests. $_"
}
Pop-Location

# 3. Rebuild Frontend
Log-Message "Rebuilding frontend..."
$frontendDir = Join-Path -Path $PSScriptRoot -ChildPath "frontend\unified_dashboard"
Push-Location $frontendDir
try {
    # Run npm run build
    $buildResult = npm run build 2>&1
    Log-Message "Build Output:"
    Log-Message ($buildResult -join "`n")
    if ($LASTEXITCODE -ne 0) {
        Log-Message "WARNING: Frontend build failed!"
    } else {
        Log-Message "SUCCESS: Frontend build completed successfully."
    }
} catch {
    Log-Message "ERROR: Failed to run frontend build. $_"
}
Pop-Location

# 4. Commit and Push
Log-Message "Checking for changes to commit..."
# Refresh status
$gitStatusNew = git status --porcelain
if ($gitStatusNew) {
    Log-Message "Staging files..."
    git add -A
    $commitMsg = "Auto-commit: Repository periodic check-in $timestamp"
    Log-Message "Committing changes with message: '$commitMsg'"
    git commit -m $commitMsg
    
    Log-Message "Pushing changes to origin main..."
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Log-Message "SUCCESS: Pushed changes to origin main."
    } else {
        Log-Message "ERROR: Git push failed with exit code $LASTEXITCODE."
    }
} else {
    Log-Message "No changes to commit and push."
}

Log-Message "Repository check-in process finished."
