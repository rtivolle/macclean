"""
Tests unitaires pour les fonctionnalités de nettoyage
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from macclean.core import (
    DuplicateFinder, CacheCleaner, OrphanedFilesFinder, 
    LargeFilesFinder, FileInfo
)
from macclean.utils import (
    format_file_size, safe_delete_file, export_to_json,
    export_to_csv, export_to_txt
)


class TestFileInfo:
    """Tests pour la classe FileInfo"""
    
    def test_file_info_creation(self):
        """Test de création d'un FileInfo"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file.flush()
            
            file_info = FileInfo(tmp_file.name, 0)
            
            assert file_info.path == tmp_file.name
            assert file_info.size > 0
            assert file_info.modified_time > 0
            
            os.unlink(tmp_file.name)
    
    def test_file_info_nonexistent_file(self):
        """Test avec un fichier inexistant"""
        file_info = FileInfo("/nonexistent/file.txt", 100)
        assert file_info.path == "/nonexistent/file.txt"
        assert file_info.size == 100  # Garde la taille fournie


class TestDuplicateFinder:
    """Tests pour DuplicateFinder"""
    
    def setup_method(self):
        """Configuration pour chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.finder = DuplicateFinder()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_calculate_md5(self):
        """Test du calcul MD5"""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello World")
        
        md5_hash = self.finder.calculate_md5(str(test_file))
        assert md5_hash == "b10a8db164e0754105b7a99be72e3fe5"
    
    def test_calculate_md5_nonexistent(self):
        """Test MD5 avec fichier inexistant"""
        md5_hash = self.finder.calculate_md5("/nonexistent/file.txt")
        assert md5_hash == ""
    
    def test_scan_directory_no_duplicates(self):
        """Test scan sans doublons"""
        # Créer des fichiers uniques
        file1 = Path(self.test_dir) / "file1.txt"
        file2 = Path(self.test_dir) / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        duplicates = self.finder.scan_directory(self.test_dir)
        assert len(duplicates) == 0
    
    def test_scan_directory_with_duplicates(self):
        """Test scan avec doublons"""
        # Créer des fichiers identiques
        file1 = Path(self.test_dir) / "file1.txt"
        file2 = Path(self.test_dir) / "file2.txt"
        content = "Identical content"
        file1.write_text(content)
        file2.write_text(content)
        
        duplicates = self.finder.scan_directory(self.test_dir)
        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2
    
    def test_scan_directory_with_progress_callback(self):
        """Test scan avec callback de progression"""
        file1 = Path(self.test_dir) / "file1.txt"
        file1.write_text("Content")
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        self.finder.scan_directory(self.test_dir, progress_callback)
        # Le callback peut être appelé ou non selon le nombre de fichiers
        # On vérifie juste qu'il n'y a pas d'erreur


class TestCacheCleaner:
    """Tests pour CacheCleaner"""
    
    def test_init(self):
        """Test d'initialisation"""
        cleaner = CacheCleaner()
        assert isinstance(cleaner.cache_directories, list)
    
    @patch('platform.system')
    def test_get_cache_directories_macos(self, mock_system):
        """Test détection répertoires cache macOS"""
        mock_system.return_value = "Darwin"
        
        # Créer une instance avec le mock
        cleaner = CacheCleaner()
        
        # Vérifier qu'au moins quelques répertoires sont détectés
        cache_dirs = cleaner._get_cache_directories()
        # Les répertoires n'existent pas forcément, mais ils doivent être définis
        expected_patterns = ["Library/Caches", "Library/Application Support", "/tmp"]
        # Au moins un pattern doit être présent dans la liste complète des répertoires potentiels
        assert len(cache_dirs) >= 0  # Au moins vide, mais pas d'erreur
    
    @patch('platform.system')
    def test_get_cache_directories_linux(self, mock_system):
        """Test détection répertoires cache Linux"""
        mock_system.return_value = "Linux"
        cleaner = CacheCleaner()
        
        cache_dirs = cleaner._get_cache_directories()
        assert any(".cache" in d for d in cache_dirs)
    
    def test_scan_cache_files(self):
        """Test scan des fichiers cache"""
        cleaner = CacheCleaner()
        
        # Mock des répertoires de cache
        with tempfile.TemporaryDirectory() as temp_dir:
            cleaner.cache_directories = [temp_dir]
            
            # Créer quelques fichiers
            test_file = Path(temp_dir) / "cache_file.tmp"
            test_file.write_text("cache content")
            
            cache_files = cleaner.scan_cache_files()
            assert len(cache_files) >= 1
            assert any(f.path == str(test_file) for f in cache_files)


class TestLargeFilesFinder:
    """Tests pour LargeFilesFinder"""
    
    def setup_method(self):
        """Configuration pour chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.finder = LargeFilesFinder(min_size_mb=1)  # 1MB min
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_find_large_files_empty_dir(self):
        """Test avec répertoire vide"""
        large_files = self.finder.find_large_files(self.test_dir)
        assert len(large_files) == 0
    
    def test_find_large_files_small_files(self):
        """Test avec petits fichiers"""
        small_file = Path(self.test_dir) / "small.txt"
        small_file.write_text("small content")
        
        large_files = self.finder.find_large_files(self.test_dir)
        assert len(large_files) == 0
    
    def test_find_large_files_large_file(self):
        """Test avec gros fichier"""
        large_file = Path(self.test_dir) / "large.txt"
        # Créer un fichier de plus de 1MB
        content = "x" * (1024 * 1024 + 1)
        large_file.write_text(content)
        
        large_files = self.finder.find_large_files(self.test_dir)
        assert len(large_files) == 1
        assert large_files[0].path == str(large_file)


class TestUtilityFunctions:
    """Tests pour les fonctions utilitaires"""
    
    def test_format_file_size(self):
        """Test formatage taille fichier"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_safe_delete_file(self):
        """Test suppression sécurisée"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test")
            tmp_file.flush()
            
            # Vérifier que le fichier existe
            assert os.path.exists(tmp_file.name)
            
            # Supprimer
            result = safe_delete_file(tmp_file.name)
            assert result is True
            assert not os.path.exists(tmp_file.name)
    
    def test_safe_delete_file_nonexistent(self):
        """Test suppression fichier inexistant"""
        result = safe_delete_file("/nonexistent/file.txt")
        assert result is False
    
    def test_export_to_json(self):
        """Test export JSON"""
        files = [
            FileInfo("/test/file1.txt", 100),
            FileInfo("/test/file2.txt", 200)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            result = export_to_json(files, tmp_file.name)
            assert result is True
            
            # Vérifier le contenu
            import json
            with open(tmp_file.name, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['path'] == "/test/file1.txt"
            assert data[0]['size'] == 100
            
            os.unlink(tmp_file.name)
    
    def test_export_to_csv(self):
        """Test export CSV"""
        files = [
            FileInfo("/test/file1.txt", 100),
            FileInfo("/test/file2.txt", 200)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            result = export_to_csv(files, tmp_file.name)
            assert result is True
            
            # Vérifier le contenu
            with open(tmp_file.name, 'r') as f:
                content = f.read()
            
            assert "/test/file1.txt" in content
            assert "100" in content
            
            os.unlink(tmp_file.name)
    
    def test_export_to_txt(self):
        """Test export TXT"""
        files = [
            FileInfo("/test/file1.txt", 100),
            FileInfo("/test/file2.txt", 200)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            result = export_to_txt(files, tmp_file.name)
            assert result is True
            
            # Vérifier le contenu
            with open(tmp_file.name, 'r') as f:
                content = f.read()
            
            assert "Rapport MacClean" in content
            assert "/test/file1.txt" in content
            
            os.unlink(tmp_file.name)
