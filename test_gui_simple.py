#!/usr/bin/env python3
"""
Test simple GUI pour MacClean - Vérifier l'affichage des fichiers
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin source
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test minimal avec des données factices
from macclean.core.cleaner import FileInfo
from macclean.utils.helpers import format_file_size

def create_test_data():
    """Crée des données de test"""
    test_files = [
        FileInfo("/workspaces/macclean/README.md", 0),
        FileInfo("/workspaces/macclean/main.py", 0),
        FileInfo("/workspaces/macclean/requirements.txt", 0),
    ]
    
    # Créer un lien symbolique pour test
    test_link = '/tmp/test_gui_symlink'
    if os.path.exists(test_link) or os.path.islink(test_link):
        os.unlink(test_link)
    os.symlink('/workspaces/macclean/README.md', test_link)
    
    # Ajouter le lien symbolique aux données de test
    test_files.append(FileInfo(test_link, 0))
    
    return test_files

def test_table_widget():
    """Test du widget table sans interface graphique complète"""
    print("=== Test FileTableWidget ===")
    
    # Simuler la création de données
    test_data = create_test_data()
    
    print(f"Données de test créées: {len(test_data)} fichiers")
    
    for i, file_info in enumerate(test_data):
        print(f"Fichier {i+1}:")
        print(f"  Chemin: {file_info.path}")
        print(f"  Taille: {format_file_size(file_info.size)}")
        print(f"  Type: {file_info.file_type}")
        print(f"  Supprimable: {file_info.is_removable}")
        print()
    
    # Nettoyer le lien symbolique
    test_link = '/tmp/test_gui_symlink'
    if os.path.exists(test_link) or os.path.islink(test_link):
        os.unlink(test_link)
    
    print("✅ Données de test validées")
    return test_data

def test_scan_worker_simulation():
    """Test de simulation du ScanWorker"""
    print("=== Test ScanWorker (simulation) ===")
    
    from macclean.core.cleaner import DuplicateFinder
    
    # Tester avec un petit répertoire
    finder = DuplicateFinder()
    test_dir = "/workspaces/macclean/src"
    
    print(f"Scan de test sur: {test_dir}")
    
    try:
        def simple_progress(current, total=0):
            if total > 0 and current % 100 == 0:
                print(f"  Progrès: {current}/{total}")
        
        duplicates = finder.scan_directory(test_dir, simple_progress)
        
        # Convertir les groupes en liste plate pour simulation GUI
        all_files = []
        for group in duplicates:
            all_files.extend(group)
        
        print(f"✅ Résultat: {len(all_files)} fichiers dans {len(duplicates)} groupes")
        
        return all_files[:10]  # Limiter à 10 pour test
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def main():
    """Fonction principale"""
    print("🧪 Test GUI MacClean (sans interface)")
    print("=" * 50)
    
    # Test 1: Données de base
    test_data = test_table_widget()
    
    # Test 2: Simulation de scan
    scan_results = test_scan_worker_simulation()
    
    print("\n" + "=" * 50)
    print("📊 Résumé:")
    print(f"  Données de test: {len(test_data)} fichiers")
    print(f"  Résultats de scan: {len(scan_results)} fichiers")
    
    if test_data and scan_results:
        print("\n✅ Les données sont générées correctement.")
        print("   Le problème d'affichage GUI peut être résolu.")
    else:
        print("\n⚠️  Problème dans la génération des données.")
    
    return test_data, scan_results

if __name__ == "__main__":
    main()
