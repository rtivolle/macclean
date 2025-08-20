"""
Configuration pour les tests pytest
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def pytest_configure(config):
    """Configuration globale des tests"""
    # Configuration pour les tests GUI
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Désactiver les tests GUI si PySide6 n'est pas disponible
    try:
        import PySide6
    except ImportError:
        config.option.markexpr = "not gui"
