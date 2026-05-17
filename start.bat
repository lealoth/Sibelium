@echo off
echo ============================================
echo    Sibelium Cognitive Architecture
echo ============================================
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instalalo desde https://python.org
    pause
    exit /b 1
)

:: Crear entorno virtual si no existe
if not exist ".venv" (
    echo [1/4] Creando entorno virtual...
    python -m venv .venv
)

:: Activar entorno
call .venv\Scripts\activate.bat

:: Instalar dependencias
echo [2/4] Instalando dependencias...
pip install -r requirements.txt --quiet

:: Descargar modelos si no existen
if not exist "models\Llama-3.1-8B-Instruct-Q4_K_M.gguf" (
    echo [3/4] Descargando modelo principal...
    echo [AVISO] Descarga manual desde HuggingFace:
    echo https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
    echo Colocalo en la carpeta models/
)

:: Iniciar
echo [4/4] Iniciando Sibelium...
python main.py

pause