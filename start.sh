#!/bin/bash

# Script de démarrage pour MacClean
# Usage: ./start.sh [--dev|--test|--install]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${GREEN}[MacClean]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[MacClean]${NC} $1"
}

error() {
    echo -e "${RED}[MacClean]${NC} $1"
}

# Vérifier que Python est installé
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log "Python $PYTHON_VERSION détecté"
    
    # Vérifier la version minimale (3.8)
    if [[ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 >= $2)}') -eq 0 ]]; then
        error "Python 3.8+ requis. Version actuelle: $PYTHON_VERSION"
        exit 1
    fi
}

# Créer et activer l'environnement virtuel
setup_venv() {
    if [ ! -d "venv" ]; then
        log "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi
    
    log "Activation de l'environnement virtuel..."
    source venv/bin/activate
}

# Installer les dépendances
install_deps() {
    log "Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ "$1" = "dev" ]; then
        log "Installation des dépendances de développement..."
        pip install pytest pytest-qt pytest-cov
    fi
}

# Lancer les tests
run_tests() {
    log "Lancement des tests..."
    export QT_QPA_PLATFORM=offscreen
    pytest tests/ -v
}

# Lancer l'application
run_app() {
    log "Lancement de MacClean..."
    python main.py
}

# Fonction principale
main() {
    case "$1" in
        --install)
            log "Installation de MacClean..."
            check_python
            setup_venv
            install_deps
            log "Installation terminée!"
            log "Utilisez './start.sh' pour lancer l'application"
            ;;
        --dev)
            log "Mode développement..."
            check_python
            setup_venv
            install_deps "dev"
            log "Environnement de développement prêt!"
            ;;
        --test)
            log "Mode test..."
            check_python
            setup_venv
            install_deps "dev"
            run_tests
            ;;
        --help|-h)
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  --install    Installation initiale"
            echo "  --dev        Configuration développement"
            echo "  --test       Lancer les tests"
            echo "  --help       Afficher cette aide"
            echo ""
            echo "Sans option: lance l'application"
            ;;
        *)
            log "Lancement de MacClean..."
            check_python
            
            if [ ! -d "venv" ]; then
                warn "Environnement virtuel non trouvé. Installation automatique..."
                setup_venv
                install_deps
            else
                source venv/bin/activate
            fi
            
            run_app
            ;;
    esac
}

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "main.py" ]; then
    error "Ce script doit être exécuté depuis le répertoire racine de MacClean"
    exit 1
fi

# Lancer la fonction principale avec tous les arguments
main "$@"
