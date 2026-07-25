@echo off
setlocal enabledelayedexpansion

echo =========================================================================
echo                FTIRdex ^& FTIRlib - Local Test Suite
echo =========================================================================
echo.

set C_STATUS=0
set PY_STATUS=0

:: 1. Building and Running C Native Tests (Unity + CTest)
echo [1/2] Compiling C Native Tests with CMake ^& CTest...
echo -------------------------------------------------------------------------
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to configure CMake.
    set C_STATUS=1
) else (
    cmake --build build --config Release > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to compile C targets.
        set C_STATUS=1
    ) else (
        ctest --test-dir build --output-on-failure -C Release
        if %ERRORLEVEL% NEQ 0 (
            set C_STATUS=1
        )
    )
)

echo.
:: 2. Running Python Tests (pytest)
echo [2/2] Running Python Tests with pytest (FTIRlib)...
echo -------------------------------------------------------------------------
python -m pytest Tests/FTIRlib --tb=short
if %ERRORLEVEL% NEQ 0 (
    set PY_STATUS=1
)

echo.
echo =========================================================================
echo                         TEST SUITE SUMMARY
echo =========================================================================
if "%C_STATUS%"=="0" (
    echo   C Native Tests ^(Unity^): PASSED
) else (
    echo   C Native Tests ^(Unity^): FAILED
)

if "%PY_STATUS%"=="0" (
    echo   Python Tests ^(pytest^): PASSED
) else (
    echo   Python Tests ^(pytest^): FAILED
)
echo =========================================================================

if "%C_STATUS%"=="0" if "%PY_STATUS%"=="0" (
    echo   RESULT: ALL SUITES PASSED SUCCESSFULLY!
    exit /b 0
)

echo   RESULT: SOME TESTS FAILED. Please review the log above.
exit /b 1
