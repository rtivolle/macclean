#!/usr/bin/env python3
"""
Test de l'affichage des fichiers dans les tables GUI
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin source
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test sans interface graphique
from macclean.core.cleaner import FileInfo
from macclean.utils.helpers import format_file_size

def test_file_info_creation():
    """Test de création des objets FileInfo"""
    print("=== Test de création des FileInfo ===")
    
    # Créer quelques fichiers de test
    test_files = [
        "/workspaces/macclean/README.md",
        "/workspaces/macclean/main.py",
        "/workspaces/macclean/requirements.txt"
    ]
    
    file_infos = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            file_info = FileInfo(file_path, 0)  # La taille sera calculée automatiquement
            file_infos.append(file_info)
            
            print(f"Fichier: {file_info.path}")
            print(f"  Taille: {format_file_size(file_info.size)}")
            print(f"  Type: {file_info.file_type}")
            print(f"  Supprimable: {file_info.is_removable}")
            print()
    
    print(f"✅ {len(file_infos)} FileInfo créés avec succès")
    return file_infos

def test_duplicate_finder():
    """Test du DuplicateFinder"""
    print("=== Test du DuplicateFinder ===")
    
    from macclean.core.cleaner import DuplicateFinder
    
    finder = DuplicateFinder()
    
    # Scanner le répertoire de travail (limité pour le test)
    test_dir = "/workspaces/macclean"
    print(f"Scan du répertoire: {test_dir}")
    
    try:
        # Utiliser un callback simple pour le progrès
        def progress_callback(current, total=0):
            if total > 0:
                print(f"Progrès: {current}/{total}")
            else:
                print(f"Fichiers traités: {current}")
        
        duplicates = finder.scan_directory(test_dir, progress_callback)
        
        print(f"✅ Scan terminé: {len(duplicates)} groupes de doublons trouvés")
        
        # Afficher quelques résultats
        for i, group in enumerate(duplicates[:3]):  # Limiter à 3 groupes
            print(f"\nGroupe {i+1}: {len(group)} fichiers")
            for file_info in group:
                print(f"  - {file_info.path} ({format_file_size(file_info.size)})")
        
        return duplicates
        
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")
        return []

def test_cache_cleaner():
    """Test du CacheCleaner"""
    print("=== Test du CacheCleaner ===")
    
    from macclean.core.cleaner import CacheCleaner
    
    cleaner = CacheCleaner()
    
    try:
        def progress_callback(current):
            print(f"Fichiers cache trouvés: {current}")
        
        cache_files = cleaner.scan_cache_files(progress_callback)
        
        print(f"✅ Scan cache terminé: {len(cache_files)} fichiers trouvés")
        
        # Afficher quelques résultats
        for file_info in cache_files[:5]:  # Limiter à 5 fichiers
            print(f"  - {file_info.path} ({format_file_size(file_info.size)})")
        
        return cache_files
        
    except Exception as e:
        print(f"❌ Erreur lors du scan cache: {e}")
        return []

def main():
    """Fonction principale de test"""
    print("🧪 Tests d'affichage MacClean")
    print("=" * 50)
    
    # Test 1: Création des FileInfo
    file_infos = test_file_info_creation()
    
    # Test 2: DuplicateFinder
    duplicates = test_duplicate_finder()
    
    # Test 3: CacheCleaner
    cache_files = test_cache_cleaner()
    
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    print(f"  FileInfo créés: {len(file_infos)}")
    print(f"  Groupes de doublons: {len(duplicates)}")
    print(f"  Fichiers cache: {len(cache_files)}")
    
    # Test d'affichage en mode texte
    if duplicates or cache_files:
        print("\n✅ Les données sont correctement générées.")
        print("   Le problème d'affichage est probablement dans l'interface graphique.")
    else:
        print("\n⚠️  Aucune donnée générée. Vérifier la logique de scan.")

if __name__ == "__main__":
    main()
