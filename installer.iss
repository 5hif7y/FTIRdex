; Inno Setup script for FTIRdex
[Setup]
AppName=FTIRdex
AppVersion=1.0.0
DefaultDirName={autopf}\FTIRdex
DefaultGroupName=FTIRdex
UninstallDisplayIcon={app}\FTIRdex.exe
Compression=lzma2
SolidCompression=yes
OutputDir=output
OutputBaseFilename=FTIRdex-Installer-x64
SetupIconFile=Icono.ico

[Files]
Source: "build\Release\FTIRdex.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\process_ftir.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\make_ico.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\Icono.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\Release\FTIRlib\*"; DestDir: "{app}\FTIRlib"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FTIRdex"; Filename: "{app}\FTIRdex.exe"
Name: "{autodesktop}\FTIRdex"; Filename: "{app}\FTIRdex.exe"
