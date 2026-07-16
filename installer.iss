; Inno Setup script for FTIRdex
#define VerFile FileOpen(SourcePath + "\VERSION")
#define AppVersion FileRead(VerFile)
#expr FileClose(VerFile)
#undef VerFile

[Setup]
AppName=FTIRdex
AppVersion={#AppVersion}
AppPublisher=Alemán Matías R. (5hif7y)
DefaultDirName={autopf}\FTIRdex
DefaultGroupName=FTIRdex
UninstallDisplayIcon={app}\FTIRdex.exe
Compression=lzma2
SolidCompression=yes
OutputDir=output
OutputBaseFilename=FTIRdex-{#AppVersion}-Installer-x64
SetupIconFile=icono.ico

; Force installation to Program Files (64-bit) instead of Program Files (x86) on 64-bit Windows
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Dirs]
; Grant standard users Modify permissions so the app can write runtime temp files (plots and CSVs) in Program Files
Name: "{app}"; Permissions: users-modify

[Files]
Source: "build\Release\FTIRdex.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\process_ftir.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\make_ico.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\icono.ico"; DestDir: "{app}"; Flags: ignoreversion
; Exclude the large historical recovery folder to optimize installation size
Source: "build\Release\FTIRlib\*"; DestDir: "{app}\FTIRlib"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "recuperacion-historica,recuperacion-historica\*"

[Icons]
Name: "{group}\FTIRdex"; Filename: "{app}\FTIRdex.exe"
Name: "{autodesktop}\FTIRdex"; Filename: "{app}\FTIRdex.exe"

[Tasks]
Name: envPath; Description: "Agregar FTIRdex a la variable de entorno PATH (permite ejecutarlo desde cmd/PowerShell)"; Flags: unchecked

[Registry]
; Append the application directory to the User's PATH environment variable
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: envPath; Flags: preservestringtype

[Run]
; Checkbox option to launch the application once the installation finishes successfully
Filename: "{app}\FTIRdex.exe"; Description: "Ejecutar FTIRdex al finalizar la instalación"; Flags: postinstall nowait skipifsilent
