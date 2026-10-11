@echo off
REM Cleanup script to remove old strategy data from databases AND strategy files
REM This will delete database files and strategy scripts for all instances
REM Fresh databases will be created when instances start

echo.
echo ========================================
echo OpenAlgo Complete Cleanup Script
echo ========================================
echo.
echo WARNING: This will delete ALL strategy data and strategy files
echo Make sure all instances are STOPPED before proceeding!
echo.
pause

cd /d "%~dp0"

echo.
echo ========================================
echo STEP 1: Deleting Database Files
echo ========================================
echo.

echo Deleting database files for Instance 3 (IndMoney - Port 5003)...
if exist "db\openalgo_3.db" del /f "db\openalgo_3.db" && echo Deleted openalgo_3.db
if exist "db\openalgo_3.db-shm" del /f "db\openalgo_3.db-shm" && echo Deleted openalgo_3.db-shm
if exist "db\openalgo_3.db-wal" del /f "db\openalgo_3.db-wal" && echo Deleted openalgo_3.db-wal
if exist "db\sandbox_3.db" del /f "db\sandbox_3.db" && echo Deleted sandbox_3.db
if exist "db\sandbox_3.db-shm" del /f "db\sandbox_3.db-shm" && echo Deleted sandbox_3.db-shm
if exist "db\sandbox_3.db-wal" del /f "db\sandbox_3.db-wal" && echo Deleted sandbox_3.db-wal

echo.
echo Deleting database files for Instance 4 (Zerodha - Port 5004)...
if exist "db\openalgo_4.db" del /f "db\openalgo_4.db" && echo Deleted openalgo_4.db
if exist "db\openalgo_4.db-shm" del /f "db\openalgo_4.db-shm" && echo Deleted openalgo_4.db-shm
if exist "db\openalgo_4.db-wal" del /f "db\openalgo_4.db-wal" && echo Deleted openalgo_4.db-wal
if exist "db\sandbox_4.db" del /f "db\sandbox_4.db" && echo Deleted sandbox_4.db
if exist "db\sandbox_4.db-shm" del /f "db\sandbox_4.db-shm" && echo Deleted sandbox_4.db-shm
if exist "db\sandbox_4.db-wal" del /f "db\sandbox_4.db-wal" && echo Deleted sandbox_4.db-wal

echo.
echo Deleting database files for Instance 5 (FivePaisa - Port 5005)...
if exist "db\openalgo_5.db" del /f "db\openalgo_5.db" && echo Deleted openalgo_5.db
if exist "db\openalgo_5.db-shm" del /f "db\openalgo_5.db-shm" && echo Deleted openalgo_5.db-shm
if exist "db\openalgo_5.db-wal" del /f "db\openalgo_5.db-wal" && echo Deleted openalgo_5.db-wal
if exist "db\sandbox_5.db" del /f "db\sandbox_5.db" && echo Deleted sandbox_5.db
if exist "db\sandbox_5.db-shm" del /f "db\sandbox_5.db-shm" && echo Deleted sandbox_5.db-shm
if exist "db\sandbox_5.db-wal" del /f "db\sandbox_5.db-wal" && echo Deleted sandbox_5.db-wal

echo.
echo ========================================
echo STEP 2: Deleting Strategy Configuration
echo ========================================
echo.

echo Deleting strategy configuration file...
if exist "strategies\strategy_configs.json" (
    del /f "strategies\strategy_configs.json" && echo Deleted strategy_configs.json
) else (
    echo No strategy configuration file found
)

echo.
echo ========================================
echo STEP 3: Deleting Strategy Script Files
echo ========================================
echo.

echo Deleting all strategy script files from strategies\scripts\...
if exist "strategies\scripts\*.py" (
    for %%F in (strategies\scripts\*.py) do (
        del /f "%%F" && echo Deleted %%~nxF
    )
) else (
    echo No strategy files found to delete
)

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Summary of deleted items:
echo - All database files (openalgo_3.db, openalgo_4.db, openalgo_5.db)
echo - All sandbox databases (sandbox_3.db, sandbox_4.db, sandbox_5.db)
echo - Strategy configuration file (strategies\strategy_configs.json)
echo - All strategy script files (*.py in strategies\scripts\)
echo.
echo Next steps:
echo 1. Start your instances again
echo 2. Fresh databases will be created automatically
echo 3. Old strategies will no longer appear
echo 4. All instances will start with ZERO strategies
echo.
pause
