# MSA Update - Backup and Apply Changes
# PowerShell script to backup old files and apply MSA adjustments

$ErrorActionPreference = "Continue"
$baseDir = "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"
Set-Location $baseDir

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "MSA UPDATE - BACKUP AND APPLY" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# Create backup folder
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFolder = "BACKUP_NATIONAL_AVG_$timestamp"
Write-Host "`nCreating backup folder: $backupFolder" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null

# Files to backup
$filesToBackup = @(
    "top10_corporate_data.csv",
    "corporate_all_zips.csv",
    "corporate_histogram_*.png",
    "corporate_weighted_averages_*.png",
    "corporate_travel_time_*.png",
    "corporate_statistical_analysis.py",
    "*.csv"
)

# Backup files
Write-Host "`nBacking up files..." -ForegroundColor Yellow
Copy-Item -Path "top10_corporate_data.csv" -Destination "$backupFolder\" -ErrorAction SilentlyContinue
Copy-Item -Path "corporate_all_zips.csv" -Destination "$backupFolder\" -ErrorAction SilentlyContinue
Copy-Item -Path "corporate_*.png" -Destination "$backupFolder\" -ErrorAction SilentlyContinue
Copy-Item -Path "*weighted*.csv" -Destination "$backupFolder\" -ErrorAction SilentlyContinue
Copy-Item -Path "dashboard_integrated.html" -Destination "$backupFolder\" -ErrorAction SilentlyContinue

Write-Host "[OK] Backup complete: $backupFolder" -ForegroundColor Green
Write-Host "$timestamp" | Out-File -FilePath "last_backup.txt"

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "APPLYING MSA ADJUSTMENTS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# Run Python update script
Write-Host "`nRunning MSA update script..." -ForegroundColor Yellow
python -u update_with_msa.py 2>&1 | Write-Host

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "BACKUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "`nBackup location: $backupFolder" -ForegroundColor Yellow
Write-Host "`nNext: Run the update script manually if needed" -ForegroundColor Yellow
Write-Host "      python update_with_msa.py" -ForegroundColor White

