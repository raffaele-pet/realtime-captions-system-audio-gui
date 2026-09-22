@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Realtime Captions - Installazione
echo  =================================
echo.

set "PY_CMD="
py -3.11 --version >nul 2>&1 && set "PY_CMD=py -3.11"
if not defined PY_CMD python --version >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
    echo ERRORE: Python 3.11 o superiore non trovato.
    echo Scaricalo da https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creazione ambiente Python isolato...
    %PY_CMD% -m venv .venv || goto :error
) else (
    echo [1/4] Ambiente Python gia presente.
)

echo [2/4] Aggiornamento strumenti di installazione...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel || goto :error

echo [3/4] Installazione dipendenze...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error

echo [4/4] Creazione icona e collegamento sul desktop...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup_windows.ps1" -AppDirectory "%~dp0." || goto :error

echo.
echo Installazione completata. Avvio Realtime Captions...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
exit /b 0

:error
echo.
echo Installazione non riuscita. Controlla il messaggio sopra e riprova.
pause
exit /b 1
