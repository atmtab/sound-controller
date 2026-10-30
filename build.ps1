# Сборка: тесты -> иконка -> exe (PyInstaller) -> установщик (Inno Setup).
# Результат: dist\SoundController\, dist-onefile\SoundController.exe, installer\Output\SoundController-Setup-*.exe
# Нативные программы пишут обычные сообщения в stderr, поэтому ошибки ловим по коду возврата.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
if ($LASTEXITCODE) { throw "Тесты не прошли" }
Remove-Item Env:QT_QPA_PLATFORM

python tools/make_icon.py build/app.ico
if ($LASTEXITCODE) { throw "Не удалось создать иконку" }

$common = @(
    "--noconfirm", "--windowed", "--name", "SoundController", "--icon", "build/app.ico",
    "--collect-all", "sounddevice", "--collect-submodules", "comtypes", "--collect-submodules", "pycaw"
)
python -m PyInstaller @common --onedir run.py
if ($LASTEXITCODE) { throw "PyInstaller (onedir) не отработал" }
python -m PyInstaller @common --onefile --distpath dist-onefile run.py
if ($LASTEXITCODE) { throw "PyInstaller (onefile) не отработал" }

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 не найден: winget install JRSoftware.InnoSetup" }
& $iscc installer\SoundController.iss
if ($LASTEXITCODE) { throw "Inno Setup не отработал" }
