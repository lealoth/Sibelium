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

:: Verificar e instalar dependencias
echo [2/4] Verificando dependencias...

:: Verificar si requirements.txt existe
if not exist "requirements.txt" (
    echo [!] requirements.txt no encontrado. Omitiendo verificacion de dependencias.
    goto :skip_deps
)

:: Verificar cada dependencia del requirements.txt
set NEED_INSTALL=0
for /f "usebackq delims=" %%p in ("requirements.txt") do (
    :: Saltar líneas vacías y comentarios
    if not "%%p"=="" (
        echo %%p | findstr /r "^#" >nul
        if errorlevel 1 (
            :: Extraer nombre del paquete (antes de ==, >=, <=, ~=, !=, o espacios)
            for /f "tokens=1 delims==><~! " %%n in ("%%p") do (
                pip show %%n >nul 2>&1
                if errorlevel 1 (
                    echo   Falta: %%n
                    set NEED_INSTALL=1
                )
            )
        )
    )
)

if %NEED_INSTALL%==1 (
    echo   Instalando dependencias faltantes...
    pip install -r requirements.txt --quiet
) else (
    echo   Todas las dependencias estan instaladas.
)

:skip_deps

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