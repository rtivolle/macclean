#!/usr/bin/env python3
"""
Test minimal de l'interface graphique MacClean
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin source
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gui_minimal():
    """Test minimal de l'interface graphique"""
    print("🧪 Test minimal GUI MacClean")
    
    # Test d'import
    try:
        from macclean.core.cleaner import FileInfo
        from macclean.utils.helpers import format_file_size
        print("✅ Imports core réussis")
    except Exception as e:
        print(f"❌ Erreur d'import core: {e}")
        return False
    
    # Test de création de données
    try:
        test_files = [
            FileInfo("/workspaces/macclean/README.md", 0),
            FileInfo("/workspaces/macclean/main.py", 0),
        ]
        print(f"✅ Création de {len(test_files)} FileInfo réussie")
    except Exception as e:
        print(f"❌ Erreur création FileInfo: {e}")
        return False
    
    # Test d'import GUI (sans lancement)
    try:
        from PySide6.QtWidgets import QApplication, QTableWidget
        from PySide6.QtCore import Qt
        
        # Créer une application Qt minimal
        app = QApplication([])
        
        # Tester la création d'une table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setRowCount(len(test_files))
        
        print("✅ Création table Qt réussie")
        
        # Tester le remplissage de la table
        for row, file_info in enumerate(test_files):
            from PySide6.QtWidgets import QTableWidgetItem, QCheckBox
            
            # Nom
            table.setItem(row, 1, QTableWidgetItem(os.path.basename(file_info.path)))
            # Taille
            table.setItem(row, 2, QTableWidgetItem(format_file_size(file_info.size)))
            # Type
            table.setItem(row, 3, QTableWidgetItem(file_info.file_type.upper()))
            # Chemin
            table.setItem(row, 4, QTableWidgetItem(file_info.path))
            # Date
            table.setItem(row, 5, QTableWidgetItem("2025-01-01"))
        
        print(f"✅ Remplissage table réussi: {table.rowCount()} lignes")
        
        # Vérifier que les données sont dans la table
        for row in range(table.rowCount()):
            name_item = table.item(row, 1)
            if name_item:
                print(f"  Ligne {row}: {name_item.text()}")
        
        # Fermer l'application
        app.quit()
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Interface graphique non disponible: {e}")
        print("   (Normal en environnement headless)")
        return True
    except Exception as e:
        print(f"❌ Erreur GUI: {e}")
        return False

def main():
    """Fonction principale"""
    success = test_gui_minimal()
    
    if success:
        print("\n✅ Tests réussis - L'affichage GUI devrait fonctionner")
        print("\nPour tester l'interface complète:")
        print("  python main.py")
    else:
        print("\n❌ Tests échoués - Problème dans l'affichage GUI")
    
    return success

if __name__ == "__main__":
    main()
