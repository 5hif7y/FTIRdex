@echo off
setlocal enabledelayedexpansion

:: 1. Read version from VERSION file
if not exist VERSION (
    echo Error: VERSION file not found!
    exit /b 1
)
set /p VERSION=<VERSION
set VERSION=%VERSION: =%
echo Packaging FTIRdex version %VERSION%...

:: 2. Build the project in Release mode using CMake
echo.
echo [1/4] Building release binary...
cmake -B build -S .
cmake --build build --config Release
if %ERRORLEVEL% neq 0 (
    echo Error: CMake build failed!
    exit /b 1
)

:: 3. Create the portable ZIP
echo.
echo [2/4] Creating portable ZIP...
set PORTABLE_DIR=FTIRdex-%VERSION%-portable
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"

:: Copy executable and python assets
copy build\Release\FTIRdex.exe "%PORTABLE_DIR%\"
copy build\Release\process_ftir.py "%PORTABLE_DIR%\"
copy build\Release\make_ico.py "%PORTABLE_DIR%\"
copy build\Release\icono.ico "%PORTABLE_DIR%\"
copy build\Release\JetBrainsMono-Regular.ttf "%PORTABLE_DIR%\"

:: Copy FTIRlib excluding the large historical folder to match installer logic
mkdir "%PORTABLE_DIR%\FTIRlib"
xcopy /E /I build\Release\FTIRlib "%PORTABLE_DIR%\FTIRlib\"
if exist "%PORTABLE_DIR%\FTIRlib\recuperacion-historica" rmdir /s /q "%PORTABLE_DIR%\FTIRlib\recuperacion-historica"

:: Compress into zip
if exist "FTIRdex-%VERSION%-portable.zip" del "FTIRdex-%VERSION%-portable.zip"
tar -a -c -f "FTIRdex-%VERSION%-portable.zip" "%PORTABLE_DIR%"
rmdir /s /q "%PORTABLE_DIR%"
echo Portable ZIP created: FTIRdex-%VERSION%-portable.zip

:: 4. Create the source code tar.gz
echo.
echo [3/4] Creating source tar.gz...
if exist "FTIRdex-%VERSION%-source.tar.gz" del "FTIRdex-%VERSION%-source.tar.gz"
git archive --format=tar.gz --prefix=FTIRdex-%VERSION%-source/ -o "FTIRdex-%VERSION%-source.tar.gz" HEAD
echo Source tar.gz created: FTIRdex-%VERSION%-source.tar.gz

:: 5. Create the Inno Setup installer
echo.
echo [4/4] Creating Inno Setup installer...
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto no_iscc

"%ISCC%" installer.iss
if %ERRORLEVEL% neq 0 (
    echo Error: Inno Setup compilation failed!
    exit /b 1
)
goto build_done

:no_iscc
echo Warning: Inno Setup ISCC.exe not found at "%ISCC%". Skipping installer build.

:build_done
echo.
echo All artifacts generated successfully:
echo   - FTIRdex-%VERSION%-portable.zip
echo   - FTIRdex-%VERSION%-source.tar.gz
if exist "FTIRdex-%VERSION%-Installer-x64.exe" (
    echo   - FTIRdex-%VERSION%-Installer-x64.exe
)
