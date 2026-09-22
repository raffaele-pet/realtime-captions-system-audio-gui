param([Parameter(Mandatory = $true)][string]$AppDirectory)

$ErrorActionPreference = 'Stop'
$appPath = [System.IO.Path]::GetFullPath($AppDirectory)
$assetsPath = Join-Path $appPath 'assets'
New-Item -ItemType Directory -Path $assetsPath -Force | Out-Null

$pngPath = Join-Path $assetsPath 'chat-room.png'
$icoPath = Join-Path $assetsPath 'chat-room.ico'
$iconUrl = 'https://img.icons8.com/?size=256&id=QfXoGJ7IiNP0&format=png'
Invoke-WebRequest -Uri $iconUrl -OutFile $pngPath -UseBasicParsing

# ICO files can contain a PNG payload. Build the small ICO header without image conversion.
$pngBytes = [System.IO.File]::ReadAllBytes($pngPath)
$stream = [System.IO.File]::Create($icoPath)
$writer = [System.IO.BinaryWriter]::new($stream)
try {
    $writer.Write([UInt16]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]1)
    $writer.Write([Byte]0)
    $writer.Write([Byte]0)
    $writer.Write([Byte]0)
    $writer.Write([Byte]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]32)
    $writer.Write([UInt32]$pngBytes.Length)
    $writer.Write([UInt32]22)
    $writer.Write($pngBytes)
} finally {
    $writer.Dispose()
    $stream.Dispose()
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'Realtime Captions.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $appPath '.venv\Scripts\pythonw.exe'
$shortcut.Arguments = '"' + (Join-Path $appPath 'main.py') + '"'
$shortcut.WorkingDirectory = $appPath
$shortcut.IconLocation = $icoPath + ',0'
$shortcut.Description = 'Sottotitoli in tempo reale dall’audio di sistema'
$shortcut.Save()

Write-Host "Collegamento creato: $shortcutPath"
