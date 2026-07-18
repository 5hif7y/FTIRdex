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
OutputDir=.
OutputBaseFilename=FTIRdex-{#AppVersion}-installer-x64
SetupIconFile=icono.ico
ChangesAssociations=yes
LicenseFile=LICENSE
WizardImageFile=assets\sidebar_banner.bmp
WizardSmallImageFile=assets\logo_top_small.bmp
WizardImageStretch=yes

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
Name: envPath; Description: "Agregar FTIRdex a la variable de entorno PATH (permite ejecutarlo desde cmd/PowerShell)"
Name: associateFiles; Description: "Asociar FTIRdex con la extensión de archivo .ftirzip (permite abrir archivos de proyecto haciendo doble clic)"

[Registry]
; Append the application directory to the User's PATH environment variable
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: envPath; Flags: preservestringtype

; File association for .ftirzip files
Root: HKA; Subkey: "Software\Classes\.ftirzip"; ValueType: string; ValueName: ""; ValueData: "FTIRdex.Project"; Flags: uninsdeletevalue; Tasks: associateFiles
Root: HKA; Subkey: "Software\Classes\FTIRdex.Project"; ValueType: string; ValueName: ""; ValueData: "FTIRdex Project File"; Flags: uninsdeletekey; Tasks: associateFiles
Root: HKA; Subkey: "Software\Classes\FTIRdex.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\FTIRdex.exe,0"; Flags: uninsdeletekey; Tasks: associateFiles
Root: HKA; Subkey: "Software\Classes\FTIRdex.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\FTIRdex.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associateFiles


[Run]
; Checkbox option to launch the application once the installation finishes successfully
Filename: "{app}\FTIRdex.exe"; Description: "Ejecutar FTIRdex al finalizar la instalación"; Flags: postinstall nowait skipifsilent

