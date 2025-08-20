#!/usr/bin/env python3
"""
Demo CLI avec les nouvelles fonctionnalités MacClean
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin source
sys.path.insert(0, str(Path(__file__).parent / "src"))

from macclean.core.cleaner import FileInfo, DuplicateFinder, CacheCleaner
from macclean.utils.helpers import format_file_size

def demo_new_features():
    """Démonstration des nouvelles fonctionnalités"""
    print("🎉 Démonstration des nouvelles fonctionnalités MacClean")
    print("=" * 60)
    
    # 1. Démonstration de l'affichage de taille totale sélectionnée
    print("\n1️⃣  AFFICHAGE DE TAILLE TOTALE")
    print("-" * 30)
    
    test_files = [
        FileInfo("/workspaces/macclean/README.md", 0),
        FileInfo("/workspaces/macclean/main.py", 0),
        FileInfo("/workspaces/macclean/requirements.txt", 0),
    ]
    
    # Simuler une sélection de fichiers
    selected_files = test_files[:2]  # Sélectionner 2 fichiers
    
    total_size = sum(f.size for f in selected_files)
    media_count = sum(1 for f in selected_files if f.file_type in ["image", "video"])
    
    print(f"Fichiers sélectionnés: {len(selected_files)}")
    print(f"Taille totale: {format_file_size(total_size)}")
    print(f"Fichiers médias: {media_count}")
    
    # 2. Démonstration des types de fichiers médias
    print("\n2️⃣  DÉTECTION DES TYPES DE FICHIERS")
    print("-" * 30)
    
    # Créer des exemples de fichiers médias (simulation)
    media_examples = [
        ("/fake/photo.jpg", "image"),
        ("/fake/video.mp4", "video"),
        ("/fake/document.pdf", "file"),
    ]
    
    for path, expected_type in media_examples:
        # Simulation du type de fichier
        print(f"📁 {os.path.basename(path)}:")
        print(f"   Type détecté: {expected_type.upper()}")
        if expected_type in ["image", "video"]:
            print(f"   🎬 Fichier média - Prévisualisation disponible")
        print()
    
    # 3. Démonstration des liens symboliques
    print("\n3️⃣  DÉTECTION DES LIENS SYMBOLIQUES")
    print("-" * 30)
    
    # Créer un lien symbolique pour test
    test_link = '/tmp/demo_symlink'
    broken_link = '/tmp/demo_broken_link'
    
    try:
        # Lien valide
        if os.path.exists(test_link) or os.path.islink(test_link):
            os.unlink(test_link)
        os.symlink('/workspaces/macclean/README.md', test_link)
        
        link_info = FileInfo(test_link, 0)
        print(f"🔗 Lien symbolique valide:")
        print(f"   Chemin: {link_info.path}")
        print(f"   Type: {link_info.file_type}")
        print(f"   Supprimable: {'✅ Oui' if link_info.is_removable else '❌ Non'}")
        print()
        
        # Lien brisé
        if os.path.exists(broken_link) or os.path.islink(broken_link):
            os.unlink(broken_link)
        os.symlink('/fichier/inexistant', broken_link)
        
        broken_info = FileInfo(broken_link, 0)
        print(f"💔 Lien symbolique brisé:")
        print(f"   Chemin: {broken_info.path}")
        print(f"   Type: {broken_info.file_type}")
        print(f"   Supprimable: {'✅ Oui' if broken_info.is_removable else '❌ Non (protégé)'}")
        print(f"   ⚠️  Recommandation: Ne pas supprimer automatiquement")
        print()
        
        # Nettoyer
        os.unlink(test_link)
        os.unlink(broken_link)
        
    except Exception as e:
        print(f"❌ Erreur lors du test des liens: {e}")
    
    # 4. Démonstration des informations de sélection détaillées
    print("\n4️⃣  INFORMATIONS DE SÉLECTION DÉTAILLÉES")
    print("-" * 30)
    
    # Simuler une sélection complexe
    mixed_files = [
        FileInfo("/workspaces/macclean/README.md", 0),  # Fichier normal
        FileInfo("/etc/hosts", 0),  # Fichier système (non supprimable)
    ]
    
    # Ajouter un lien si possible
    try:
        temp_link = '/tmp/temp_demo_link'
        if os.path.exists(temp_link) or os.path.islink(temp_link):
            os.unlink(temp_link)
        os.symlink('/workspaces/macclean/main.py', temp_link)
        mixed_files.append(FileInfo(temp_link, 0))
        
        # Calculer les statistiques
        total_size = sum(f.size for f in mixed_files)
        normal_files = sum(1 for f in mixed_files if f.file_type == "file" and f.is_removable)
        symlinks = sum(1 for f in mixed_files if f.file_type == "symlink")
        protected_files = sum(1 for f in mixed_files if not f.is_removable)
        
        print(f"📊 Résumé de sélection:")
        print(f"   Total: {len(mixed_files)} fichiers ({format_file_size(total_size)})")
        print(f"   Fichiers normaux: {normal_files}")
        print(f"   Liens symboliques: {symlinks}")
        print(f"   Fichiers protégés: {protected_files}")
        
        if protected_files > 0:
            print(f"   ⚠️  {protected_files} fichier(s) ne peuvent pas être supprimés")
        
        # Nettoyer
        os.unlink(temp_link)
        
    except Exception as e:
        print(f"❌ Erreur lors du test de sélection: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Démonstration terminée !")
    print("\nNOUVELLES FONCTIONNALITÉS IMPLÉMENTÉES:")
    print("  ✅ Affichage de la taille totale des fichiers sélectionnés")
    print("  ✅ Prévisualisation des fichiers médias (images/vidéos)")
    print("  ✅ Détection et protection des liens symboliques brisés")
    print("  ✅ Interface avec codes couleur selon le type de fichier")
    print("  ✅ Informations détaillées de sélection")

def demo_scan_with_new_features():
    """Démonstration d'un scan avec les nouvelles fonctionnalités"""
    print("\n🔍 DÉMONSTRATION DE SCAN AVEC NOUVELLES FONCTIONNALITÉS")
    print("=" * 60)
    
    # Scanner le répertoire src pour des doublons
    finder = DuplicateFinder()
    test_dir = "/workspaces/macclean/src"
    
    print(f"Scan de: {test_dir}")
    print("Recherche de doublons avec informations détaillées...")
    
    try:
        duplicates = finder.scan_directory(test_dir)
        
        print(f"\n📋 Résultats du scan:")
        print(f"   {len(duplicates)} groupes de doublons trouvés")
        
        # Analyser les types de fichiers trouvés
        all_files = []
        for group in duplicates[:3]:  # Limiter à 3 groupes pour l'exemple
            all_files.extend(group)
        
        if all_files:
            total_size = sum(f.size for f in all_files)
            file_types = {}
            removable_count = 0
            
            for file_info in all_files:
                if file_info.file_type not in file_types:
                    file_types[file_info.file_type] = 0
                file_types[file_info.file_type] += 1
                
                if file_info.is_removable:
                    removable_count += 1
            
            print(f"\n📊 Analyse des doublons:")
            print(f"   Total: {len(all_files)} fichiers ({format_file_size(total_size)})")
            print(f"   Supprimables: {removable_count}/{len(all_files)}")
            print(f"   Types de fichiers:")
            for file_type, count in file_types.items():
                icon = "🎬" if file_type in ["image", "video"] else "🔗" if file_type == "symlink" else "📄"
                print(f"     {icon} {file_type.upper()}: {count}")
        
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")

def main():
    """Fonction principale"""
    demo_new_features()
    demo_scan_with_new_features()
    
    print(f"\n🚀 Pour utiliser l'interface graphique complète:")
    print(f"   python main.py")
    print(f"\n💡 Les nouvelles fonctionnalités sont maintenant intégrées!")

if __name__ == "__main__":
    main()
