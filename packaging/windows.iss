#ifndef AppVersion
  #define AppVersion "0.1.1"
#endif

[Setup]
AppId={{196490BA-05F3-433C-B7A8-2A9C46BB3F50}
AppName=小雅
AppVersion={#AppVersion}
AppPublisher=nicemilos
AppPublisherURL=https://github.com/nicemilos/gf
DefaultDirName={localappdata}\Programs\Xiaoya
DefaultGroupName=小雅
UsePreviousGroup=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\release
OutputBaseFilename=Xiaoya-{#AppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app-icon.ico
UninstallDisplayIcon={app}\Xiaoya.exe
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："; Flags: unchecked

[Files]
Source: "..\dist\Xiaoya\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\小雅"; Filename: "{app}\Xiaoya.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\小雅"; Filename: "{app}\Xiaoya.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[InstallDelete]
; Remove only shortcuts created by the previous version, never user data.
Type: files; Name: "{autodesktop}\小雅桌宠.lnk"
Type: files; Name: "{userprograms}\小雅桌宠\小雅桌宠.lnk"
Type: dirifempty; Name: "{userprograms}\小雅桌宠"

[Run]
Filename: "{app}\Xiaoya.exe"; Description: "启动小雅"; Flags: nowait postinstall skipifsilent

; User memory and Windows QSettings are deliberately outside {app}.
; Upgrading or uninstalling does not erase the user's conversations or API key.
