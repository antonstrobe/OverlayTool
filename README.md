# LineGuide — инструмент выравнивания линий для геометрии детекторов CERN

[Репозиторий на GitHub](https://github.com/antonstrobe/OverlayTool)
Лицензия — MIT

---

## Описание (RU)

**LineGuide** — это небольшая утилита захвата экрана и наложения направляющих линий, разработанная для инженерных групп CERN. Она упрощает ручное совмещение контрольных точек при калибровке и выравнивании детекторов Большого адронного коллайдера (LHC), ускоряя расчёт геометрических констант и повышая точность трек‑реконструкции.

### Возможности

* Привязка линий к сетке экрана одним кликом.
* Субпиксельные сдвиги (до 0,1 px) клавишами‑стрелками.
* Кроссплатформенно протестировано на Windows 10+; код совместим с Linux/macOS.
* Распространяется в открытом виде без внешних зависимостей ROOT/CMSSW.

### Python и зависимости

* **Python ≥ 3.9 (64‑bit)**.
* `pip install -r requirements.txt` устанавливает: PyQt5, opencv‑python, numpy, mss, pynput, pyinstaller.

### Сборка .exe для Windows

1. Установите Python 3.9 (x64) и добавьте его в `PATH`.
2. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/antonstrobe/OverlayTool.git
   cd OverlayTool
   ```
3. Установите зависимости:

   ```bash
   python -m pip install -r requirements.txt
   ```
4. Соберите исполняемый файл (два варианта):

   * \*\*Скрипт \*\*\`\` (автоматически генерирует версию и иконку):

     ```cmd
     build.bat
     ```
   * **PyInstaller напрямую**:

     ```bash
     pyinstaller --onefile --windowed --icon=app.ico overlay.py
     ```
5. Готовый `overlaytool.exe` появится в папке `dist`.

---

## Description (EN)

**LineGuide** is a small screen‑overlay utility created at CERN to speed up manual alignment of detector fiducials for the Large Hadron Collider. By drawing ultra‑sharp guide lines on top of any image it helps engineers match reference points faster, improving geometry recognition and reducing calibration time.

### Features

* One‑click snap‑to‑grid calibration.
* Sub‑pixel nudging (0.1 px) with arrow keys.
* Tested on Windows 10+; code is portable to Linux/macOS.
* Pure Python; no ROOT/CMSSW runtime needed.

### Python & Dependencies

* **Python ≥ 3.9 (64‑bit)**.
* Install dependencies with `pip install -r requirements.txt` (PyQt5, opencv‑python, numpy, mss, pynput, pyinstaller).

### Build .exe on Windows

1. Install 64‑bit Python 3.9 and ensure it is in your `PATH`.
2. Clone the repository:

   ```bash
   git clone https://github.com/antonstrobe/OverlayTool.git
   cd OverlayTool
   ```
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```
4. Build the executable (choose one):

   * \`\`\*\* wrapper\*\*:

     ```cmd
     build.bat
     ```
   * **Direct PyInstaller call**:

     ```bash
     pyinstaller --onefile --windowed --icon=app.ico overlay.py
     ```
5. The resulting `overlaytool.exe` will be located in the `dist` directory.

---

## Quick Start (Windows)

1. Запустите `overlaytool.exe` из `dist` или скачайте готовый релиз.
2. Нажмите **Calibrate**, выберите оси.
3. Совмещайте контрольные точки, используя стрелки и `Space` для фиксации линий.

---

## Демонстрация / Demo

| Step | Screenshot                                                                   | CERN‑slang Commentary                                                                                                              |
| ---- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 1    | ![UI hint](docs/images/1.png)             | **Tooltip**: напоминалка, что *Ctrl — фиксировать*, *Shift — зачистить*. Появляется в «tray» до начала сессии выравнивания.        |
| 2    | ![Barrel view — raw](docs/images/2.png)   | **Barrel view**: черновая прокладка трёх track‑лайнов по hits слоёв Pixel/Strip; пересечка пока грубая.                            |
| 3    | ![Barrel view — tuned](docs/images/3.png) | **Fine‑tune**: линии «дожаты» до общего вертекса; красный cross‑hair — ROI, зелёный circle — vertex‑candidate после ручного nudge. |
| 4    | ![Endcap projection](docs/images/4.png)   | **Endcap projection**: тот же event в r‑φ; концентрические overlay‑кольца позволяют быстро чекнуть ∆z и радиальный вынос.          |
| 5    | ![Feedback panel](docs/images/5.png)      | **Feedback dialog**: сводка после `Ctrl`: displaced‑vertex check (2 matches) и combo‑скрин barrel + endcap.                        |



---

*Разработано в рамках инициатив CERN по открытому программному обеспечению. Пожалуйста, открывайте Issues и Pull Requests!*
