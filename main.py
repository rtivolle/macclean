#!/usr/bin/env python3
"""
MacClean - Application GUI pour nettoyer le stockage Mac/PC
Point d'entrée principal de l'application
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from macclean.gui.main_window import MacCleanApp
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def main():
    """Point d'entrée principal de l'application MacClean"""
    # Configuration de l'application Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("MacClean")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MacClean")
    
    # Créer et afficher la fenêtre principale
    window = MacCleanApp()
    window.show()
    
    # Lancer la boucle d'événements
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
