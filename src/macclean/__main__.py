"""
Point d'entrée principal pour l'exécution en module
python -m macclean
"""

from .gui.main_window import MacCleanApp
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys

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
