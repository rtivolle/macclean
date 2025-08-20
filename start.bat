@echo off
REM Script de démarrage pour MacClean sur Windows
REM Usage: start.bat [install|dev|test]

setlocal enabledelayedexpansion

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://www.python.org/
    pause
    exit /b 1
)

REM Vérifier qu'on est dans le bon répertoire
if not exist "main.py" (
    echo [ERREUR] Ce script doit être exécuté depuis le répertoire racine de MacClean
    pause
    exit /b 1
)

if "%1"=="install" goto :install
if "%1"=="dev" goto :dev
if "%1"=="test" goto :test
if "%1"=="help" goto :help
if "%1"=="-h" goto :help
if "%1"=="/?" goto :help

REM Mode normal - lancer l'application
echo [MacClean] Lancement de MacClean...

REM Vérifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo [MacClean] Environnement virtuel non trouvé. Installation automatique...
    goto :setup_venv
)

REM Activer l'environnement virtuel et lancer l'app
call venv\Scripts\activate.bat
python main.py
goto :end

:install
echo [MacClean] Installation de MacClean...
call :setup_venv
call :install_deps
echo [MacClean] Installation terminée!
echo Utilisez 'start.bat' pour lancer l'application
goto :end

:dev
echo [MacClean] Mode développement...
call :setup_venv
call :install_deps dev
echo [MacClean] Environnement de développement prêt!
goto :end

:test
echo [MacClean] Mode test...
call :setup_venv
call :install_deps dev
echo [MacClean] Lancement des tests...
call venv\Scripts\activate.bat
set QT_QPA_PLATFORM=offscreen
pytest tests/ -v
goto :end

:help
echo Usage: %0 [option]
echo.
echo Options:
echo   install    Installation initiale
echo   dev        Configuration développement
echo   test       Lancer les tests
echo   help       Afficher cette aide
echo.
echo Sans option: lance l'application
goto :end

:setup_venv
if not exist "venv" (
    echo [MacClean] Création de l'environnement virtuel...
    python -m venv venv
)
call venv\Scripts\activate.bat
goto :eof

:install_deps
echo [MacClean] Installation des dépendances...
python -m pip install --upgrade pip
pip install -r requirements.txt

if "%1"=="dev" (
    echo [MacClean] Installation des dépendances de développement...
    pip install pytest pytest-qt pytest-cov
)
goto :eof

:end
pause
