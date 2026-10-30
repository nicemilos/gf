#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{196490BA-05F3-433C-B7A8-2A9C46BB3F50}
AppName=小雅桌宠
AppVersion={#AppVersion}
AppPublisher=nicemilos
AppPublisherURL=https://github.com/nicemilos/gf
DefaultDirName={localappdata}\Programs\Xiaoya
DefaultGroupName=小雅桌宠
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\release
OutputBaseFilename=Xiaoya-{#AppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Xiaoya.exe
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\Xiaoya\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\小雅桌宠"; Filename: "{app}\Xiaoya.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\小雅桌宠"; Filename: "{app}\Xiaoya.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Xiaoya.exe"; Description: "Launch Xiaoya"; Flags: nowait postinstall skipifsilent

; User memory and Windows QSettings are deliberately outside {app}.
; Upgrading or uninstalling does not erase the user's conversations or API key.
