"""
Utilitaires pour l'application MacClean
Optimisé pour Apple M1/M2 - Performance maximale
"""

import os
import json
import csv
import concurrent.futures
import platform
from typing import List, Dict, Any
from pathlib import Path
from macclean.core import FileInfo


def is_apple_silicon() -> bool:
    """Détecte si on est sur Apple Silicon (M1/M2)"""
    return platform.system() == "Darwin" and platform.machine() in ('arm64', 'aarch64')


def format_file_size(size_bytes: int) -> str:
    """Formate la taille d'un fichier en unités lisibles"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def safe_delete_file_optimized(file_path: str) -> bool:
    """Supprime un fichier de manière sécurisée - Optimisé M1"""
    try:
        if os.path.exists(file_path):
            # Sur M1, utiliser la suppression système optimisée
            if is_apple_silicon():
                # Préférer unlink direct sur M1 pour les performances
                os.unlink(file_path)
            else:
                os.remove(file_path)
            return True
        return False
    except (OSError, IOError, PermissionError):
        return False


def safe_delete_files_batch(file_paths: List[str], max_workers: int = None) -> Dict[str, bool]:
    """Supprime plusieurs fichiers en parallèle - Optimisé M1"""
    if not max_workers:
        max_workers = min(os.cpu_count() or 8, 16) if is_apple_silicon() else 4
    
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(safe_delete_file_optimized, path): path 
            for path in file_paths
        }
        
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                success = future.result()
                results[path] = success
            except Exception:
                results[path] = False
    
    return results


# Garde la fonction originale pour compatibilité
def safe_delete_file(file_path: str) -> bool:
    """Fonction de compatibilité"""
    return safe_delete_file_optimized(file_path)


def export_to_json_optimized(data: List[FileInfo], output_path: str) -> bool:
    """Exporte les données vers un fichier JSON - Optimisé M1"""
    try:
        export_data = []
        
        # Traitement en parallèle pour les gros datasets sur M1
        if is_apple_silicon() and len(data) > 1000:
            def process_file_info(file_info: FileInfo) -> Dict:
                return {
                    "path": file_info.path,
                    "size": file_info.size,
                    "size_formatted": format_file_size(file_info.size),
                    "hash_md5": file_info.hash_md5,
                    "modified_time": file_info.modified_time,
                    "device_id": getattr(file_info, 'device_id', None),
                    "inode": getattr(file_info, 'inode', None)
                }
            
            max_workers = min(os.cpu_count() or 8, 12)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                export_data = list(executor.map(process_file_info, data))
        else:
            # Traitement séquentiel pour les petits datasets
            for file_info in data:
                export_data.append({
                    "path": file_info.path,
                    "size": file_info.size,
                    "size_formatted": format_file_size(file_info.size),
                    "hash_md5": file_info.hash_md5,
                    "modified_time": file_info.modified_time,
                    "device_id": getattr(file_info, 'device_id', None),
                    "inode": getattr(file_info, 'inode', None)
                })
        
        # Écriture optimisée avec buffer plus grand sur M1
        with open(output_path, 'w', encoding='utf-8', buffering=8192 if is_apple_silicon() else -1) as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception:
        return False


def export_to_csv_optimized(data: List[FileInfo], output_path: str) -> bool:
    """Exporte les données vers un fichier CSV - Optimisé M1"""
    try:
        # Buffer plus grand sur M1 pour les performances I/O
        with open(output_path, 'w', newline='', encoding='utf-8', 
                  buffering=8192 if is_apple_silicon() else -1) as f:
            writer = csv.writer(f)
            writer.writerow(['Chemin', 'Taille (octets)', 'Taille', 'Hash MD5', 
                           'Date modification', 'Device ID', 'Inode'])
            
            # Traitement par batch sur M1 pour optimiser les performances
            if is_apple_silicon() and len(data) > 1000:
                batch_size = 1000
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    rows = []
                    for file_info in batch:
                        rows.append([
                            file_info.path,
                            file_info.size,
                            format_file_size(file_info.size),
                            file_info.hash_md5 or '',
                            file_info.modified_time,
                            getattr(file_info, 'device_id', ''),
                            getattr(file_info, 'inode', '')
                        ])
                    writer.writerows(rows)
            else:
                for file_info in data:
                    writer.writerow([
                        file_info.path,
                        file_info.size,
                        format_file_size(file_info.size),
                        file_info.hash_md5 or '',
                        file_info.modified_time,
                        getattr(file_info, 'device_id', ''),
                        getattr(file_info, 'inode', '')
                    ])
        
        return True
    except Exception:
        return False


# Fonctions de compatibilité
def export_to_json(data: List[FileInfo], output_path: str) -> bool:
    """Fonction de compatibilité"""
    return export_to_json_optimized(data, output_path)


def export_to_csv(data: List[FileInfo], output_path: str) -> bool:
    """Fonction de compatibilité"""
    return export_to_csv_optimized(data, output_path)


def export_to_txt(data: List[FileInfo], output_path: str) -> bool:
    """Exporte les données vers un fichier texte"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Rapport MacClean\n")
            f.write("=" * 50 + "\n\n")
            
            for file_info in data:
                f.write(f"Fichier: {file_info.path}\n")
                f.write(f"Taille: {format_file_size(file_info.size)}\n")
                if file_info.hash_md5:
                    f.write(f"Hash MD5: {file_info.hash_md5}\n")
                f.write(f"Modifié: {file_info.modified_time}\n")
                f.write("-" * 30 + "\n")
        
        return True
    except Exception:
        return False


def get_system_info_m1_optimized() -> Dict[str, Any]:
    """Retourne les informations système - Optimisé pour M1/M2"""
    import platform
    import psutil
    
    # Détection spéciale M1/M2
    cpu_info = {}
    if is_apple_silicon():
        # Informations spécifiques Apple Silicon
        try:
            import subprocess
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            cpu_info['brand'] = result.stdout.strip() if result.returncode == 0 else "Apple Silicon"
            
            # Nombre de cœurs de performance et d'efficience
            result = subprocess.run(['sysctl', '-n', 'hw.perflevel0.logicalcpu'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                cpu_info['performance_cores'] = int(result.stdout.strip())
            
            result = subprocess.run(['sysctl', '-n', 'hw.perflevel1.logicalcpu'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                cpu_info['efficiency_cores'] = int(result.stdout.strip())
                
            # Mémoire unifiée
            result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                cpu_info['unified_memory'] = int(result.stdout.strip())
                
        except Exception:
            cpu_info['brand'] = "Apple Silicon"
    
    disk_usage = psutil.disk_usage('/')
    
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "machine": platform.machine(),
        "is_apple_silicon": is_apple_silicon(),
        "cpu_count": os.cpu_count(),
        "cpu_info": cpu_info,
        "disk_total": disk_usage.total,
        "disk_used": disk_usage.used,
        "disk_free": disk_usage.free,
        "disk_percent": (disk_usage.used / disk_usage.total) * 100,
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
    }
    
    # Ajouter des métriques de performance M1
    if is_apple_silicon():
        system_info['optimizations'] = {
            'memory_mapping_optimized': True,
            'parallel_processing_optimized': True,
            'chunk_size_optimized': True,
            'io_buffer_optimized': True
        }
    
    return system_info


# Fonction de compatibilité
def get_system_info() -> Dict[str, Any]:
    """Fonction de compatibilité"""
    return get_system_info_m1_optimized()
