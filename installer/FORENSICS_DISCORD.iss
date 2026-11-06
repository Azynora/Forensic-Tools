#ifndef BundleDir
  #define BundleDir "..\dist\FORENSICS_DISCORD"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist\github-release"
#endif

#define AppName "FORENSICS_DISCORD"
#define AppVersion "1.2.0"
#define AppPublisher "Truong Trieu Vy"
#define AppExe "fdctl_runtime\FORENSICS_DISCORD.exe"

[Setup]
AppId={{8D82F581-8730-4F44-87AF-2027012A0472}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\FORENSICS_DISCORD
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutputDir}
OutputBaseFilename=FORENSICS_DISCORD_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "--gui"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "--gui"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent
