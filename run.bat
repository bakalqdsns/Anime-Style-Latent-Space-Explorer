@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  Anime Visual Research Engine — Run Script
:: ============================================================
::  Double-click this file to run (auto-detects Docker or falls back to native).
::  All errors are shown before exiting so you can read them.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

set "PYTHON=python"
set "MODE="
set "AUTO_OPEN=true"

:: Try to set UTF-8; silently skip if it fails (e.g. no admin)
chcp 65001 >nul 2>&1

:: ------------------------------------------------------------
::  Parse arguments
:: ------------------------------------------------------------
:parse_args
if "%~1"=="" goto main
if /i "%~1"=="--native"   set "MODE=native"    & shift & goto parse_args
if /i "%~1"=="--docker"   set "MODE=docker"    & shift & goto parse_args
if /i "%~1"=="--no-open"   set "AUTO_OPEN=false" & shift & goto parse_args
if /i "%~1"=="-h"          goto usage
if /i "%~1"=="--help"      goto usage
echo Unknown option: %~1
echo.
goto usage

:usage
echo.
echo  Usage: %~nx0 [OPTIONS]
echo.
echo  OPTIONS:
echo    --docker     Force Docker Compose mode
echo    --native     Force native mode (no Docker)
echo    --no-open    Do not auto-open browser
echo    -h, --help   Show this help message
echo.
echo  Double-click to auto-detect and run.
echo.
pause
goto :eof

:: ------------------------------------------------------------
::  Main entry point
:: ------------------------------------------------------------
:main
echo ============================================================
echo  Anime Visual Research Engine
echo ============================================================
echo.

if /i "%MODE%"=="native" goto run_native

:: Auto-detect Docker mode
echo [INFO] Checking Docker availability...
docker info >nul 2>&1
if errorlevel 1 (
    echo   Docker not running — falling back to native mode.
    echo   To use Docker, start Docker Desktop and run: run.bat --docker
    echo.
    goto run_native
)

docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo   Docker Compose not installed — falling back to native mode.
        echo   To use Docker, install Docker Compose and run: run.bat --docker
        echo.
        goto run_native
    )
    set "COMPOSE_CMD=docker-compose"
) else (
    set "COMPOSE_CMD=docker compose"
)

goto run_docker

:: ------------------------------------------------------------
::  Docker Compose mode
:: ------------------------------------------------------------
:run_docker
echo [1/3] Checking environment file...
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\.env.example" (
        copy /Y "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
        echo.
        echo   ERROR: .env was created but is empty.
        echo   Please open .env and fill in your API keys, then run this script again.
        echo.
        pause
        goto :eof
    ) else (
        echo   ERROR: .env.example not found.
        echo.
        pause
        goto :eof
    )
)

echo [2/3] Starting services [PostgreSQL, Qdrant, Redis, Backend, Frontend]...
echo   This may take a while on first run (pulling images)...

cd /d "%PROJECT_ROOT%"
start "Docker Compose" /min cmd /c "%COMPOSE_CMD% up"

echo [3/3] Waiting for services to be ready...
echo   - Backend API:  http://localhost:8000
echo   - API Docs:     http://localhost:8000/docs
echo   - Frontend:     http://localhost:5173
echo.

set "MAX_WAIT=120"
set "WAITED=0"

:wait_backend
ping -n 6 127.0.0.1 >nul 2>&1
set /a WAITED+=5
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if !WAITED! LSS %MAX_WAIT% (
        goto wait_backend
    ) else (
        echo.
        echo   WARNING: Backend did not respond in %MAX_WAIT%s.
        echo   Check logs with: docker compose logs -f backend
    )
) else (
    echo   Backend ready.
)

set "WAITED=0"

:wait_frontend
ping -n 6 127.0.0.1 >nul 2>&1
set /a WAITED+=5
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    if !WAITED! LSS %MAX_WAIT% (
        goto wait_frontend
    ) else (
        echo   WARNING: Frontend did not respond in %MAX_WAIT%s.
    )
) else (
    echo   Frontend ready.
)

echo.
echo ============================================================
echo  All services started successfully!
echo ============================================================
echo.
if /i "%AUTO_OPEN%"=="true" (
    echo Opening browser...
    start http://localhost:5173
)
echo.
echo  Stop services:  docker compose down
echo  View logs:      docker compose logs -f
echo  Restart:        docker compose restart
echo.
pause
goto :eof

:: ------------------------------------------------------------
::  Native mode (no Docker)
:: ------------------------------------------------------------
:run_native
echo [INFO] Running in native mode (no Docker)
echo.

:: Find Python
echo [1/7] Checking Python...
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON=py"
    %PYTHON% --version >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: Python not found. Please install Python 3.10+ from https://python.org
        echo.
        pause
        goto :eof
    )
)
for /f "delims=" %%v in ('%PYTHON% --version 2^>nul') do echo   %%v

:: Find Node.js
echo [2/7] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Node.js not found. Please install Node.js 18+ from https://nodejs.org
    echo.
    pause
    goto :eof
)
for /f "delims=" %%v in ('node --version 2^>nul') do echo   %%v

:: Check pip dependencies
echo [3/7] Checking Python dependencies...
set "DEPS_MISSING="
%PYTHON% -c "import fastapi" 2>nul
if errorlevel 1 set "DEPS_MISSING=!DEPS_MISSING! fastapi"
%PYTHON% -c "import pydantic_settings" 2>nul
if errorlevel 1 set "DEPS_MISSING=!DEPS_MISSING! pydantic-settings"
%PYTHON% -c "import uvicorn" 2>nul
if errorlevel 1 set "DEPS_MISSING=!DEPS_MISSING! uvicorn"
%PYTHON% -c "import sqlalchemy" 2>nul
if errorlevel 1 set "DEPS_MISSING=!DEPS_MISSING! sqlalchemy"
%PYTHON% -c "import torch" 2>nul
if errorlevel 1 set "DEPS_MISSING=!DEPS_MISSING! torch"

if not "!DEPS_MISSING!"=="" (
    echo   Missing packages: !DEPS_MISSING!
    echo   Installing now...
    if exist "%BACKEND_DIR%\requirements.txt" (
        %PYTHON% -m pip install --quiet -r "%BACKEND_DIR%\requirements.txt"
        if errorlevel 1 (
            echo.
            echo   ERROR: Failed to install dependencies.
            echo   Try manually: cd backend ^&^& pip install -r requirements.txt
            echo.
            pause
            goto :eof
        )
        echo   Dependencies installed.
    ) else (
        echo.
        echo   ERROR: requirements.txt not found at %BACKEND_DIR%
        echo.
        pause
        goto :eof
    )
) else (
    echo   All core dependencies found.
)

:: Check environment file
echo [4/7] Checking environment file...
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\.env.example" (
        copy /Y "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
        echo.
        echo   ERROR: .env was created but is empty.
        echo   Please open .env and fill in your API keys, then run this script again.
        echo.
        pause
        goto :eof
    )
)
echo   .env OK

:: Check external services
echo [5/7] Checking external services...
set "EXTERNAL_OK=true"

netstat -ano ^| findstr ":5432" ^| findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: PostgreSQL not running on port 5432
    echo           Set DATABASE_URL in .env to use SQLite instead
    set "EXTERNAL_OK=false"
) else (
    echo   PostgreSQL OK: port 5432
)

netstat -ano ^| findstr ":6333" ^| findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: Qdrant not running on port 6333
    echo           Vector search will use fallback mode
    set "EXTERNAL_OK=false"
) else (
    echo   Qdrant OK: port 6333
)

netstat -ano ^| findstr ":6379" ^| findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: Redis not running on port 6379
    echo           Celery task queue disabled
    set "EXTERNAL_OK=false"
) else (
    echo   Redis OK: port 6379
)

if "!EXTERNAL_OK!"=="false" (
    echo.
    echo   Some services are not running.
    echo   Backend will start with fallback modes.
    echo   For full features, run Docker mode: run.bat --docker
    echo.
)

:: Create data directories
echo [6/7] Creating data directories...
for %%d in (data data\raw data\frames data\cache data\cache\embeddings data\cache\axes data\output) do (
    if not exist "%PROJECT_ROOT%\%%d" (
        mkdir "%PROJECT_ROOT%\%%d" 2>nul
    )
)
echo   Done.

:: Start Backend
echo [7/7] Starting Backend (port 8000)...
start "Backend [Anime Engine]" cmd /k "cd /d "%BACKEND_DIR%" && %PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend
echo   Waiting for backend...
set "WAITED=0"

:wait_backend_native
ping -n 4 127.0.0.1 >nul 2>&1
set /a WAITED+=3
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if !WAITED! LSS 30 goto wait_backend_native
) else (
    echo   Backend ready.
)

:: Install frontend dependencies if needed
echo.
echo   Checking frontend dependencies...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo   Installing frontend dependencies [first run only]...
    cd /d "%FRONTEND_DIR%"
    call npm install --silent
    cd /d "%PROJECT_ROOT%"
    if errorlevel 1 (
        echo.
        echo   ERROR: npm install failed.
        echo.
        pause
        goto :eof
    )
    echo   Dependencies installed.
) else (
    echo   Dependencies OK.
)

:: Start Frontend
echo   Starting Frontend (port 5173)...
start "Frontend [Anime Engine]" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

:: Wait for frontend
set "WAITED=0"

:wait_frontend_native
ping -n 4 127.0.0.1 >nul 2>&1
set /a WAITED+=3
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    if !WAITED! LSS 30 goto wait_frontend_native
) else (
    echo   Frontend ready.
)

echo.
echo ============================================================
echo  All services started successfully!
echo ============================================================
echo.
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Frontend:     http://localhost:5173
echo.
if /i "%AUTO_OPEN%"=="true" (
    echo Opening browser...
    start http://localhost:5173
)
echo.
echo  Stop: close the [Backend] and [Frontend] terminal windows
echo.
pause
goto :eof
