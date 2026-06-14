# ============================================================
#  TriVerse AI — Desktop Shortcut Creator
#  Run once: right-click > "Run with PowerShell"
#  Creates: Desktop\TriVerse AI.lnk
# ============================================================

$projectRoot  = "f:\TriVerse-ML-main\TriVerse-ML-main"
$vbsLauncher  = Join-Path $projectRoot "TriVerse_AI.vbs"
$iconFile     = Join-Path $projectRoot "frontend\unified_dashboard\app_icon.ico"
$desktopPath  = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "TriVerse AI.lnk"

# Verify the VBS launcher exists
if (-not (Test-Path $vbsLauncher)) {
    Write-Host "[ERROR] Launcher not found: $vbsLauncher" -ForegroundColor Red
    Write-Host "Make sure you have the TriVerse_AI.vbs in the project root." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create the shortcut object
$wshell    = New-Object -ComObject WScript.Shell
$shortcut  = $wshell.CreateShortcut($shortcutPath)

# Target = wscript.exe running the VBS silently
$shortcut.TargetPath       = "wscript.exe"
$shortcut.Arguments        = "`"$vbsLauncher`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description      = "Launch TriVerse AI Platform (ML + FastAPI + Ollama)"
$shortcut.WindowStyle      = 1   # 1=Normal, 3=Maximized, 7=Minimized

# Use custom icon if available, else fall back to wscript icon
if (Test-Path $iconFile) {
    $shortcut.IconLocation = "$iconFile,0"
} else {
    $shortcut.IconLocation = "wscript.exe,0"
}

$shortcut.Save()

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   TriVerse AI shortcut created! ✓    ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Location : $shortcutPath" -ForegroundColor Green
Write-Host "  Launcher : $vbsLauncher"  -ForegroundColor Gray
Write-Host "  Icon     : $iconFile"     -ForegroundColor Gray
Write-Host ""
Write-Host "  Double-click 'TriVerse AI' on your Desktop to start." -ForegroundColor Yellow
Write-Host ""
