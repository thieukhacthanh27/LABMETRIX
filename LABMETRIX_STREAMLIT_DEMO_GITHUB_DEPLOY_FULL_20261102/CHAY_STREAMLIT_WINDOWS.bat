@echo off
setlocal
cd /d "%~dp0"
title LABMETRIX - STREAMLIT DEMO
chcp 65001 >nul
echo ================================================
echo LABMETRIX STREAMLIT DEMO - CHAY TRÊN WINDOWS
echo ================================================
where py >nul 2>&1
if %errorlevel%==0 (
 set "PYCMD=py -3.12"
) else (
 set "PYCMD=python"
)
if not exist ".venv\Scripts\python.exe" (
 echo [1/3] Tao moi truong Python...
 %PYCMD% -m venv ".venv"
 if errorlevel 1 goto :error
)
echo [2/3] Cai thu vien...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo [3/3] Chay Streamlit, mo trinh duyet tai http://localhost:8501
echo Nhan Ctrl+C de dung.
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py
if errorlevel 1 goto :error
goto :end
:error
echo [LOI] Khong the khoi dong. Kiem tra Python 3.12 / internet.
pause
:end
endlocal
