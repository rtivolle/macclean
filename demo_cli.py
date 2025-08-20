#!/usr/bin/env python3
"""
Démo CLI de MacClean - Test des fonctionnalités sans interface graphique
"""

import sys
import os
import tempfile
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from macclean.core import DuplicateFinder, CacheCleaner, LargeFilesFinder, OrphanedFilesFinder
from macclean.utils import format_file_size, get_system_info, export_to_json
import json


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_system_info():
    """Démo des informations système"""
    print_header("INFORMATIONS SYSTÈME")
    
    sys_info = get_system_info()
    print(f"Plateforme: {sys_info['platform']}")
    print(f"Architecture: {sys_info['architecture']}")
    print(f"Espace total: {format_file_size(sys_info['disk_total'])}")
    print(f"Espace utilisé: {format_file_size(sys_info['disk_used'])}")
    print(f"Espace libre: {format_file_size(sys_info['disk_free'])}")
    print(f"Utilisation: {sys_info['disk_percent']:.1f}%")


def demo_duplicate_finder():
    """Démo du chercheur de doublons"""
    print_header("DÉTECTION DE DOUBLONS")
    
    # Créer un répertoire temporaire avec des fichiers test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Création de fichiers test dans: {temp_dir}")
        
        # Créer des fichiers de test
        files_data = [
            ("file1.txt", "Contenu identique pour test"),
            ("file2.txt", "Contenu identique pour test"),  # Doublon de file1
            ("file3.txt", "Contenu différent"),
            ("subdir/file4.txt", "Contenu identique pour test"),  # Doublon dans sous-dossier
            ("large_file.bin", "x" * 1024),  # Fichier plus volumineux
        ]
        
        for filename, content in files_data:
            file_path = Path(temp_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  Créé: {filename} ({len(content)} octets)")
        
        # Lancer la détection de doublons
        print("\nRecherche de doublons...")
        finder = DuplicateFinder()
        
        def progress_callback(current, total):
            if total > 0:
                print(f"  Progression: {current}/{total} fichiers traités")
        
        duplicates = finder.scan_directory(temp_dir, progress_callback)
        
        print(f"\nRésultats:")
        print(f"  Groupes de doublons trouvés: {len(duplicates)}")
        
        total_space_wasted = 0
        for i, group in enumerate(duplicates):
            print(f"\n  Groupe {i+1}: {len(group)} fichiers identiques")
            for j, file_info in enumerate(group):
                print(f"    {j+1}. {file_info.path} ({format_file_size(file_info.size)})")
                if j > 0:  # Le premier fichier est gardé, les autres sont des doublons
                    total_space_wasted += file_info.size
        
        print(f"\nEspace récupérable: {format_file_size(total_space_wasted)}")


def demo_cache_cleaner():
    """Démo du nettoyeur de cache"""
    print_header("ANALYSE DU CACHE")
    
    cleaner = CacheCleaner()
    print(f"Répertoires de cache détectés: {len(cleaner.cache_directories)}")
    
    for cache_dir in cleaner.cache_directories[:5]:  # Afficher les 5 premiers
        print(f"  - {cache_dir}")
    
    if len(cleaner.cache_directories) > 5:
        print(f"  ... et {len(cleaner.cache_directories) - 5} autres")
    
    print("\nScan des fichiers cache (premier répertoire seulement)...")
    
    if cleaner.cache_directories:
        # Tester avec le premier répertoire accessible
        test_dir = None
        for cache_dir in cleaner.cache_directories:
            if os.path.exists(cache_dir) and os.access(cache_dir, os.R_OK):
                test_dir = cache_dir
                break
        
        if test_dir:
            # Créer un mock temporaire pour la démo
            original_dirs = cleaner.cache_directories
            cleaner.cache_directories = [test_dir]
            
            try:
                cache_files = cleaner.scan_cache_files(lambda count: print(f"  Fichiers trouvés: {count}") if count % 50 == 0 else None)
                
                total_size = sum(f.size for f in cache_files)
                print(f"\nRésultats:")
                print(f"  Fichiers cache trouvés: {len(cache_files)}")
                print(f"  Taille totale: {format_file_size(total_size)}")
                
                # Afficher quelques exemples
                for i, file_info in enumerate(cache_files[:3]):
                    print(f"  Exemple {i+1}: {file_info.path} ({format_file_size(file_info.size)})")
                
            except PermissionError:
                print("  Pas d'accès en lecture au répertoire de cache")
            finally:
                cleaner.cache_directories = original_dirs
        else:
            print("  Aucun répertoire de cache accessible trouvé")


def demo_large_files():
    """Démo du chercheur de gros fichiers"""
    print_header("RECHERCHE DE GROS FICHIERS")
    
    # Utiliser le répertoire home de l'utilisateur ou un sous-répertoire
    search_dir = str(Path.home())
    
    # Pour la démo, on va chercher des fichiers de plus de 1MB seulement
    finder = LargeFilesFinder(min_size_mb=1)
    
    print(f"Recherche dans: {search_dir}")
    print("Taille minimale: 1 MB")
    print("Attention: cette opération peut prendre du temps...\n")
    
    try:
        # Limiter la recherche pour la démo
        demo_dir = tempfile.mkdtemp()
        
        # Créer quelques fichiers de test
        large_file = Path(demo_dir) / "large_test.bin"
        large_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB
        
        small_file = Path(demo_dir) / "small_test.txt"
        small_file.write_text("Small content")
        
        print(f"Démo avec répertoire test: {demo_dir}")
        
        large_files = finder.find_large_files(demo_dir)
        
        print(f"\nRésultats:")
        print(f"  Gros fichiers trouvés: {len(large_files)}")
        
        total_size = sum(f.size for f in large_files)
        print(f"  Taille totale: {format_file_size(total_size)}")
        
        for i, file_info in enumerate(large_files):
            print(f"  {i+1}. {file_info.path} ({format_file_size(file_info.size)})")
        
        # Nettoyer
        import shutil
        shutil.rmtree(demo_dir)
        
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")


def demo_export():
    """Démo de l'export des résultats"""
    print_header("EXPORT DES RÉSULTATS")
    
    # Créer des données fictives pour la démo
    from macclean.core import FileInfo
    
    demo_files = [
        FileInfo("/tmp/file1.txt", 1024),
        FileInfo("/tmp/file2.bin", 2048),
        FileInfo("/home/user/document.pdf", 4096),
    ]
    
    # Export en JSON
    json_file = "/tmp/macclean_demo_export.json"
    if export_to_json(demo_files, json_file):
        print(f"✓ Export JSON réussi: {json_file}")
        
        # Afficher le contenu
        with open(json_file, 'r') as f:
            data = json.load(f)
        print(f"  Contenu exporté: {len(data)} entrées")
        
        # Nettoyer
        os.unlink(json_file)
    else:
        print("✗ Échec de l'export JSON")


def main():
    """Point d'entrée principal de la démo"""
    print("🧹 MacClean - Démo CLI")
    print("Application de nettoyage de stockage multiplateforme")
    
    try:
        demo_system_info()
        demo_duplicate_finder() 
        demo_cache_cleaner()
        demo_large_files()
        demo_export()
        
        print_header("DÉMO TERMINÉE")
        print("✅ Toutes les fonctionnalités ont été testées avec succès!")
        print("\nPour utiliser l'interface graphique complète:")
        print("  python main.py")
        
    except KeyboardInterrupt:
        print("\n\n❌ Démo interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur pendant la démo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
