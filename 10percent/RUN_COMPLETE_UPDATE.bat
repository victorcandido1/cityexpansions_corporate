@echo off
REM Complete MSA Update - Backup, Update Data, Regenerate Charts
cd /d "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"

echo.
echo ================================================================================
echo MSA UPDATE - COMPLETE PROCESS
echo ================================================================================
echo.

REM Step 1: Backup
echo Step 1: Creating backup...
powershell -ExecutionPolicy Bypass -File BACKUP_AND_UPDATE.ps1

REM Step 2: Update data
echo.
echo Step 2: Applying MSA adjustments...
python update_with_msa.py
if errorlevel 1 (
    echo ERROR: MSA update failed!
    pause
    exit /b 1
)

REM Step 3: Regenerate charts
echo.
echo Step 3: Regenerating corporate statistical charts...
python corporate_statistical_analysis.py
if errorlevel 1 (
    echo WARNING: Chart generation had issues
)

REM Step 4: Update travel time charts
echo.
echo Step 4: Updating travel time charts...
python create_corporate_travel_time_weighted_charts.py
if errorlevel 1 (
    echo WARNING: Travel time chart update had issues
)

echo.
echo ================================================================================
echo UPDATE COMPLETE!
echo ================================================================================
echo.
echo Check the following:
echo   - Backup folder created
echo   - top10_corporate_data.csv updated
echo   - Charts regenerated
echo   - Dashboard still works
echo.
pause

