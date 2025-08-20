"""
Tests pour l'interface graphique
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Configuration du path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from macclean.gui import MacCleanApp
from macclean.core import FileInfo


@pytest.fixture(scope="module")
def app():
    """Fixture pour l'application Qt"""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


class TestMacCleanApp:
    """Tests pour l'application principale"""
    
    def test_app_creation(self, app):
        """Test création de l'application"""
        window = MacCleanApp()
        assert window.windowTitle() == "MacClean - Nettoyeur de stockage"
        assert window.tabs.count() == 4  # 4 onglets
        window.close()
    
    def test_tabs_creation(self, app):
        """Test création des onglets"""
        window = MacCleanApp()
        
        tab_titles = []
        for i in range(window.tabs.count()):
            tab_titles.append(window.tabs.tabText(i))
        
        expected_titles = ["Doublons", "Cache", "Fichiers orphelins", "Gros fichiers"]
        assert tab_titles == expected_titles
        window.close()
    
    @patch('macclean.gui.main_window.QFileDialog.getExistingDirectory')
    def test_browse_duplicate_directory(self, mock_dialog, app):
        """Test sélection répertoire doublons"""
        window = MacCleanApp()
        
        # Mock du dialogue
        mock_dialog.return_value = "/test/directory"
        
        window.browse_duplicate_directory()
        
        assert "Répertoire: /test/directory" in window.duplicate_dir_label.text()
        window.close()
    
    def test_file_table_widget(self, app):
        """Test du widget table des fichiers"""
        window = MacCleanApp()
        
        # Tester la table des doublons
        table = window.duplicates_table
        assert table.columnCount() == 5
        
        # Tester l'ajout de fichiers
        test_files = [
            FileInfo("/test/file1.txt", 100),
            FileInfo("/test/file2.txt", 200)
        ]
        
        table.populate_table(test_files)
        assert table.rowCount() == 2
        
        window.close()
    
    def test_select_all_functionality(self, app):
        """Test sélection/désélection de tous les fichiers"""
        window = MacCleanApp()
        table = window.duplicates_table
        
        # Ajouter des fichiers test
        test_files = [
            FileInfo("/test/file1.txt", 100),
            FileInfo("/test/file2.txt", 200)
        ]
        table.populate_table(test_files)
        
        # Tester sélection de tous
        table.select_all(True)
        selected = table.get_selected_files()
        assert len(selected) == 2
        
        # Tester désélection de tous
        table.select_all(False)
        selected = table.get_selected_files()
        assert len(selected) == 0
        
        window.close()
    
    @patch('macclean.gui.main_window.ScanWorker')
    @patch('macclean.gui.main_window.QThread')
    def test_start_scan(self, mock_thread, mock_worker, app):
        """Test démarrage d'un scan"""
        window = MacCleanApp()
        
        # Mock des objets
        mock_worker_instance = Mock()
        mock_thread_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        mock_thread.return_value = mock_thread_instance
        
        window.start_scan("duplicates", {"directory": "/test"})
        
        # Vérifier que le worker et thread sont créés
        mock_worker.assert_called_once_with("duplicates", {"directory": "/test"})
        mock_thread.assert_called_once()
        
        window.close()
    
    @patch('macclean.gui.main_window.export_to_json')
    @patch('macclean.gui.main_window.QFileDialog.getSaveFileName')
    def test_export_results(self, mock_save_dialog, mock_export, app):
        """Test export des résultats"""
        window = MacCleanApp()
        
        # Préparer des données test
        test_files = [FileInfo("/test/file1.txt", 100)]
        window.duplicates_table.populate_table(test_files)
        
        # Mock du dialogue de sauvegarde
        mock_save_dialog.return_value = ("/test/export.json", "JSON (*.json)")
        mock_export.return_value = True
        
        window.export_results()
        
        # Vérifier que l'export est appelé
        mock_export.assert_called_once()
        
        window.close()


class TestScanWorker:
    """Tests pour le worker de scan"""
    
    @patch('macclean.gui.main_window.DuplicateFinder')
    def test_scan_worker_duplicates(self, mock_finder_class):
        """Test worker pour scan doublons"""
        from macclean.gui.main_window import ScanWorker
        
        # Mock du finder
        mock_finder = Mock()
        mock_finder.scan_directory.return_value = [[FileInfo("/test/file1.txt", 100)]]
        mock_finder_class.return_value = mock_finder
        
        worker = ScanWorker("duplicates", {"directory": "/test"})
        worker.run()
        
        # Vérifier que le scan est appelé
        mock_finder.scan_directory.assert_called_once_with("/test", progress_callback=worker._progress_callback)
    
    @patch('macclean.gui.main_window.CacheCleaner')
    def test_scan_worker_cache(self, mock_cleaner_class):
        """Test worker pour scan cache"""
        from macclean.gui.main_window import ScanWorker
        
        # Mock du cleaner
        mock_cleaner = Mock()
        mock_cleaner.scan_cache_files.return_value = [FileInfo("/test/cache.tmp", 50)]
        mock_cleaner_class.return_value = mock_cleaner
        
        worker = ScanWorker("cache", {})
        worker.run()
        
        # Vérifier que le scan est appelé
        mock_cleaner.scan_cache_files.assert_called_once()
    
    def test_scan_worker_stop(self):
        """Test arrêt du worker"""
        from macclean.gui.main_window import ScanWorker
        
        worker = ScanWorker("duplicates", {})
        assert worker.should_stop is False
        
        worker.stop()
        assert worker.should_stop is True
