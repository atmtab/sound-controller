<p align="center">
  <img src="assets/logo.png" alt="Sound Controller" width="160">
</p>

# Sound Controller

Трей-приложение для Windows 11 в стиле старого лампового радиоприёмника. Показывает запущенные приложения и позволяет назначить каждому своё устройство вывода звука: проводные наушники, Bluetooth-колонку или виртуальный кабель для видеозвонков.

Каждое приложение подключается к устройству кабелем: тяните штекер на нужный блок. Чтобы вернуть устройство по умолчанию, бросьте штекер в пустое место.

У каждого блока-устройства справа есть ползунок громкости (мышью или колесом). Он меняет общую громкость устройства в Windows.

## Установка

Скачайте установщик `SoundController-Setup-<версия>.exe`, запустите его и следуйте шагам. Права администратора не нужны, в мастере можно включить автозапуск с Windows.

### Из исходников

Нужен Python 3.12.

```bash
pip install -r requirements.txt
python -m sound_controller.main
```

Иконка появляется в трее, клик по ней открывает панель.

## Звук в видеозвонки (VB-Cable)

1. Установите бесплатный драйвер [VB-Cable](https://vb-audio.com/Cable/) и перезагрузите компьютер. Он не входит в состав программы.
2. Подключите нужное приложение (плеер, браузер) к блоку **CABLE Input**.
3. В программе для звонков выберите микрофоном **CABLE Output**.
4. Сам звонок выводите на наушники, а не в CABLE Input, иначе собеседники услышат себя.

Чтобы слышать у себя то, что уходит в звонок, включите тумблер «Монитор в наушниках» и выберите устройство. Звук копируется с CABLE Output с небольшой задержкой.

## Как это работает и ограничения

- Выбор устройства для приложения использует недокументированный интерфейс Windows (тот же, что в «Микшере громкости»). Обновление Windows может его сломать.
- Если звук после смены устройства не переключился, перезапустите воспроизведение в приложении.
- Приложения, свёрнутые в трей без окна, появляются в списке после включения «Все процессы» или после первого выбора устройства.
- Выбор запоминается по имени exe в `%APPDATA%\SoundController\config.json` и применяется заново, когда приложение или устройство появляется снова.

## Сборка

Нужны Python 3.12 с зависимостями из `requirements.txt`, PyInstaller и [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`).

```powershell
.\build.ps1
```

Скрипт запускает тесты, рисует иконку и собирает:

- `dist\SoundController\` — приложение папкой;
- `dist-onefile\SoundController.exe` — один портативный файл;
- `installer\Output\SoundController-Setup-<версия>.exe` — установщик.

## Разработка

```bash
python -m sound_controller.audio.devices    # устройства вывода
python -m sound_controller.audio.sessions   # запущенные приложения
python -m sound_controller.audio.routing    # текущее назначение устройств
python -m pytest
```

## Сторонние компоненты

Проект использует [PySide6](https://doc.qt.io/qtforpython-6/) (LGPLv3), [pycaw](https://github.com/AndreMiras/pycaw) (MIT), [comtypes](https://github.com/enthought/comtypes) (MIT), [psutil](https://github.com/giampaolo/psutil) (BSD-3-Clause) и [sounddevice](https://github.com/spatialaudio/python-sounddevice) (MIT). Собранные файлы включают библиотеки Qt, которые распространяются на условиях LGPLv3.

## Лицензия

[MIT](LICENSE)
