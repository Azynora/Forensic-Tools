#ifndef BundleDir
  #define BundleDir "..\dist\ForensicsSuite"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist\github-release"
#endif

#define AppName "Forensics Suite"
#define AppVersion "1.4.2"
#define AppPublisher "Truong Trieu Vy"
#define AppExe "fdctl_runtime\ForensicsSuite.exe"

[Setup]
AppId={{8D82F581-8730-4F44-87AF-2027012A0472}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Forensics Suite
DefaultGroupName={#AppName}
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutputDir}
OutputBaseFilename=ForensicsSuite_Setup
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
Filename: "{app}\{#AppExe}"; Parameters: "--gui"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent unchecked
