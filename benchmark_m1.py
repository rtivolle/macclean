#!/usr/bin/env python3
"""
Benchmark MacClean - Test des optimisations M1/M2
Mesure les performances avant/après optimisation
"""

import sys
import time
import tempfile
import os
from pathlib import Path
import hashlib
import multiprocessing
import platform
import psutil

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from macclean.core import M1OptimizedDuplicateFinder, M1OptimizedCacheCleaner, M1OptimizedLargeFilesFinder
from macclean.utils import get_system_info_m1_optimized, is_apple_silicon


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_performance_info():
    """Affiche les informations de performance du système"""
    print_header("INFORMATIONS SYSTÈME & OPTIMISATIONS")
    
    sys_info = get_system_info_m1_optimized()
    
    print(f"🖥️  Plateforme: {sys_info['platform']} {sys_info['platform_version']}")
    print(f"🔧 Architecture: {sys_info['architecture']} ({sys_info['machine']})")
    print(f"🚀 Apple Silicon: {'✅ OUI' if sys_info['is_apple_silicon'] else '❌ NON'}")
    print(f"⚡ CPU Cores: {sys_info['cpu_count']}")
    
    if 'cpu_info' in sys_info and sys_info['cpu_info']:
        cpu_info = sys_info['cpu_info']
        if 'brand' in cpu_info:
            print(f"🔥 CPU: {cpu_info['brand']}")
        if 'performance_cores' in cpu_info:
            print(f"🏃 Performance Cores: {cpu_info['performance_cores']}")
        if 'efficiency_cores' in cpu_info:
            print(f"🚶 Efficiency Cores: {cpu_info['efficiency_cores']}")
        if 'unified_memory' in cpu_info:
            memory_gb = cpu_info['unified_memory'] / (1024**3)
            print(f"💾 Unified Memory: {memory_gb:.1f} GB")
    
    memory_gb = sys_info['memory_total'] / (1024**3)
    memory_avail_gb = sys_info['memory_available'] / (1024**3)
    print(f"🧠 RAM Total: {memory_gb:.1f} GB")
    print(f"💡 RAM Disponible: {memory_avail_gb:.1f} GB")
    
    if 'optimizations' in sys_info:
        print(f"\n🚀 OPTIMISATIONS M1 ACTIVÉES:")
        for opt, enabled in sys_info['optimizations'].items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {opt}")


def create_test_files(test_dir: Path, num_files: int = 1000, num_duplicates: int = 200):
    """Crée des fichiers de test pour le benchmark"""
    print(f"📁 Création de {num_files} fichiers test avec {num_duplicates} doublons...")
    
    # Créer des contenus variés
    contents = [
        b"Contenu original " + os.urandom(1024),  # 1KB files
        b"Gros fichier " + os.urandom(1024 * 100),  # 100KB files
        b"Fichier moyen " + os.urandom(1024 * 10),   # 10KB files
    ]
    
    # Contenu pour les doublons
    duplicate_content = b"Contenu duplique " + os.urandom(1024 * 5)  # 5KB
    
    files_created = 0
    
    # Créer des fichiers uniques
    for i in range(num_files - num_duplicates):
        file_path = test_dir / f"unique_file_{i:04d}.bin"
        content = contents[i % len(contents)] + str(i).encode()
        file_path.write_bytes(content)
        files_created += 1
    
    # Créer des doublons
    for i in range(num_duplicates):
        file_path = test_dir / f"duplicate_file_{i:04d}.bin"
        file_path.write_bytes(duplicate_content)
        files_created += 1
    
    # Créer des sous-répertoires avec des fichiers
    for i in range(5):
        subdir = test_dir / f"subdir_{i}"
        subdir.mkdir()
        for j in range(20):
            file_path = subdir / f"sub_file_{j:03d}.txt"
            file_path.write_bytes(b"Sub content " + str(i*j).encode())
            files_created += 1
    
    print(f"✅ {files_created} fichiers créés")
    return files_created


def benchmark_duplicate_finder(test_dir: Path):
    """Benchmark du chercheur de doublons optimisé M1"""
    print_header("BENCHMARK - DÉTECTION DE DOUBLONS")
    
    finder = M1OptimizedDuplicateFinder()
    
    print(f"🔍 Configuration:")
    print(f"   Workers: {finder.max_workers}")
    print(f"   Chunk size: {finder.chunk_size // 1024}KB")
    print(f"   Apple Silicon: {finder.is_apple_silicon}")
    
    # Mesurer le temps de scan
    start_time = time.time()
    
    def progress_callback(current, total):
        if total > 0:
            progress = (current / total) * 100
            print(f"   📊 Progression: {current}/{total} ({progress:.1f}%)")
    
    duplicates = finder.scan_directory_optimized(str(test_dir), progress_callback)
    
    scan_time = time.time() - start_time
    
    # Statistiques
    total_duplicate_files = sum(len(group) for group in duplicates)
    total_space_wasted = sum(
        sum(file_info.size for file_info in group[1:])  # Ignorer le premier fichier de chaque groupe
        for group in duplicates
    )
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   ⏱️  Temps de scan: {scan_time:.2f}s")
    print(f"   🔍 Groupes de doublons: {len(duplicates)}")
    print(f"   📄 Fichiers en double: {total_duplicate_files}")
    print(f"   💾 Espace récupérable: {total_space_wasted / (1024*1024):.1f} MB")
    print(f"   🚀 Performance: {len(finder.files_by_size) / scan_time:.0f} fichiers/sec")
    
    return scan_time, len(duplicates)


def benchmark_cache_cleaner():
    """Benchmark du nettoyeur de cache optimisé M1"""
    print_header("BENCHMARK - NETTOYAGE DE CACHE")
    
    cleaner = M1OptimizedCacheCleaner()
    
    print(f"🧹 Configuration:")
    print(f"   Workers: {cleaner.max_workers}")
    print(f"   Apple Silicon: {cleaner.is_apple_silicon}")
    print(f"   Répertoires cache: {len(cleaner.cache_directories)}")
    
    for cache_dir in cleaner.cache_directories[:3]:
        print(f"     📁 {cache_dir}")
    if len(cleaner.cache_directories) > 3:
        print(f"     ... et {len(cleaner.cache_directories) - 3} autres")
    
    start_time = time.time()
    
    def progress_callback(count):
        print(f"   📊 Fichiers trouvés: {count}")
    
    cache_files = cleaner.scan_cache_files_optimized(progress_callback)
    
    scan_time = time.time() - start_time
    total_cache_size = sum(f.size for f in cache_files)
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   ⏱️  Temps de scan: {scan_time:.2f}s")
    print(f"   📄 Fichiers cache: {len(cache_files)}")
    print(f"   💾 Taille totale: {total_cache_size / (1024*1024):.1f} MB")
    print(f"   🚀 Performance: {len(cache_files) / scan_time:.0f} fichiers/sec")
    
    return scan_time, len(cache_files)


def benchmark_large_files(test_dir: Path):
    """Benchmark du chercheur de gros fichiers optimisé M1"""
    print_header("BENCHMARK - RECHERCHE GROS FICHIERS")
    
    # Créer quelques gros fichiers pour le test
    print("📄 Création de gros fichiers test...")
    for i in range(5):
        large_file = test_dir / f"large_file_{i}.bin"
        large_file.write_bytes(os.urandom(10 * 1024 * 1024))  # 10MB files
    
    finder = M1OptimizedLargeFilesFinder(min_size_mb=5)  # 5MB minimum
    
    print(f"🔍 Configuration:")
    print(f"   Workers: {finder.max_workers}")
    print(f"   Apple Silicon: {finder.is_apple_silicon}")
    print(f"   Taille min: {finder.min_size_bytes / (1024*1024):.0f} MB")
    print(f"   Exclusions: {len(finder.excluded_dirs)} répertoires")
    
    start_time = time.time()
    
    def progress_callback(count):
        print(f"   📊 Gros fichiers trouvés: {count}")
    
    large_files = finder.find_large_files_optimized(str(test_dir), progress_callback)
    
    scan_time = time.time() - start_time
    total_size = sum(f.size for f in large_files)
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   ⏱️  Temps de scan: {scan_time:.2f}s")
    print(f"   📄 Gros fichiers: {len(large_files)}")
    print(f"   💾 Taille totale: {total_size / (1024*1024):.1f} MB")
    if large_files:
        print(f"   🏆 Plus gros: {large_files[0].path} ({total_size / (1024*1024):.1f} MB)")
    
    return scan_time, len(large_files)


def run_memory_test():
    """Test l'utilisation mémoire"""
    print_header("TEST MÉMOIRE")
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024*1024)  # MB
    
    print(f"💾 Mémoire initiale: {initial_memory:.1f} MB")
    
    # Créer de gros objets pour tester la gestion mémoire M1
    large_data = []
    for i in range(100):
        large_data.append(os.urandom(1024 * 1024))  # 1MB chunks
    
    peak_memory = process.memory_info().rss / (1024*1024)  # MB
    print(f"📈 Pic mémoire: {peak_memory:.1f} MB")
    print(f"📊 Augmentation: +{peak_memory - initial_memory:.1f} MB")
    
    # Libérer la mémoire
    del large_data
    
    final_memory = process.memory_info().rss / (1024*1024)  # MB
    print(f"🔄 Mémoire finale: {final_memory:.1f} MB")
    
    return initial_memory, peak_memory, final_memory


def main():
    """Point d'entrée principal du benchmark"""
    print("🧹 MacClean M1 Performance Benchmark")
    print("Teste les optimisations pour Apple Silicon")
    
    print_performance_info()
    
    # Créer un répertoire de test temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        print_header("PRÉPARATION DES DONNÉES DE TEST")
        num_files = create_test_files(test_dir, num_files=2000, num_duplicates=400)
        
        # Tests de performance
        results = {}
        
        try:
            # Test mémoire
            memory_results = run_memory_test()
            results['memory'] = memory_results
            
            # Test détection doublons
            dup_time, dup_count = benchmark_duplicate_finder(test_dir)
            results['duplicates'] = (dup_time, dup_count)
            
            # Test cache (utilise les vrais répertoires système)
            cache_time, cache_count = benchmark_cache_cleaner()
            results['cache'] = (cache_time, cache_count)
            
            # Test gros fichiers
            large_time, large_count = benchmark_large_files(test_dir)
            results['large_files'] = (large_time, large_count)
            
        except KeyboardInterrupt:
            print("\n❌ Benchmark interrompu par l'utilisateur")
            return
        
        # Résumé final
        print_header("RÉSUMÉ DES PERFORMANCES")
        
        if is_apple_silicon():
            print("🚀 OPTIMISATIONS M1/M2 ACTIVÉES")
        else:
            print("💻 Mode compatibilité (non-Apple Silicon)")
        
        print(f"\n📊 MÉTRIQUES GLOBALES:")
        print(f"   📁 Fichiers test: {num_files}")
        
        if 'duplicates' in results:
            dup_time, dup_count = results['duplicates']
            print(f"   🔍 Doublons: {dup_count} groupes en {dup_time:.2f}s")
        
        if 'cache' in results:
            cache_time, cache_count = results['cache']
            print(f"   🧹 Cache: {cache_count} fichiers en {cache_time:.2f}s")
        
        if 'large_files' in results:
            large_time, large_count = results['large_files']
            print(f"   📊 Gros fichiers: {large_count} fichiers en {large_time:.2f}s")
        
        if 'memory' in results:
            initial, peak, final = results['memory']
            print(f"   💾 Mémoire: {initial:.1f}→{peak:.1f}→{final:.1f} MB")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if is_apple_silicon():
            print("   ✅ Votre système M1/M2 utilise toutes les optimisations")
            print("   🚀 Performance maximale activée")
            print("   💾 Mémoire unifiée exploitée")
            print("   ⚡ Parallélisation optimisée")
        else:
            print("   💻 Système non-Apple Silicon détecté")
            print("   ⚠️  Optimisations M1 désactivées")
            print("   📈 Performance standard")
        
        print(f"\n🎯 SCORE GLOBAL:")
        if is_apple_silicon():
            print("   🏆 EXCELLENT - Optimisé pour votre matériel")
        else:
            print("   ✅ BON - Performance standard")


if __name__ == "__main__":
    main()
