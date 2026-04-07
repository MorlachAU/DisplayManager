; DisplayPal — Inno Setup Installer Script
; Requires Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Compile with: ISCC.exe installer.iss

#define MyAppName "DisplayPal"
#define MyAppVersion "1.2.2"
#define MyAppPublisher "MouseWheel Digital"
#define MyAppURL "https://www.mousewheeldigital.com/"
#define MyAppExeName "DisplayPal.exe"
#define MyAppSourceDir "dist\DisplayPal"

[Setup]
; NOTE: AppId is intentionally kept from the DisplayManager era so that
; installing DisplayPal over an existing DisplayManager install performs
; a clean upgrade (uninstalls the old one, removes old shortcuts, then
; installs the new one).
AppId={{8E4F2B3A-1C5D-4E6F-A7B8-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://github.com/MorlachAU/DisplayPal
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=DisplayPal_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; NOTE: Autostart is handled inside the app (autostart.sync_autostart) on
; every launch, reading the user's config. The installer deliberately does
; not write HKCU directly because admin-mode installs would write to the
; wrong user's profile.

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
