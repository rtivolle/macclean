"""
Tests d'initialisation du package
"""

def test_package_import():
    """Test import du package principal"""
    try:
        import macclean
        assert macclean.__version__ == "1.0.0"
    except ImportError:
        assert False, "Impossible d'importer le package macclean"


def test_core_imports():
    """Test import des modules core"""
    try:
        from macclean.core import (
            DuplicateFinder, CacheCleaner, 
            OrphanedFilesFinder, LargeFilesFinder, FileInfo
        )
        assert True
    except ImportError as e:
        assert False, f"Impossible d'importer les modules core: {e}"


def test_utils_imports():
    """Test import des utilitaires"""
    try:
        from macclean.utils import (
            format_file_size, safe_delete_file,
            export_to_json, export_to_csv, export_to_txt
        )
        assert True
    except ImportError as e:
        assert False, f"Impossible d'importer les utilitaires: {e}"


def test_gui_imports():
    """Test import de l'interface graphique"""
    try:
        from macclean.gui import MacCleanApp
        assert True
    except ImportError as e:
        # L'import peut échouer si PySide6 n'est pas installé
        # Ce n'est pas critique pour les tests de base
        print(f"Import GUI échoué (normal si PySide6 non installé): {e}")
