# Associate .ftirzip files with FTIRdex.exe (Portable) - No Administrator Privileges Required
$exePath = "$PSScriptRoot\FTIRdex.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "FTIRdex.exe not found in this folder! Make sure to run this script from the same directory where FTIRdex.exe is located."
    exit
}
New-Item -Path "HKCU:\Software\Classes\.ftirzip" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\.ftirzip" -Name "" -Value "FTIRdex.Project"
New-Item -Path "HKCU:\Software\Classes\FTIRdex.Project" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\FTIRdex.Project" -Name "" -Value "FTIRdex Project File"
New-Item -Path "HKCU:\Software\Classes\FTIRdex.Project\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\FTIRdex.Project\DefaultIcon" -Name "" -Value "$exePath,0"
New-Item -Path "HKCU:\Software\Classes\FTIRdex.Project\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\FTIRdex.Project\shell\open\command" -Name "" -Value """$exePath"" ""%1"""
Write-Host "Success: .ftirzip files associated with FTIRdex.exe (Portable)!"

