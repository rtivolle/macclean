"""
Module core pour les fonctionnalités de nettoyage
Optimisé pour Apple M1/M2 - Utilisation maximale des performances
"""

import os
import hashlib
import platform
import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import List, Dict, Tuple, Optional, AsyncIterator
from dataclasses import dataclass, field
import psutil
import mmap
import threading
from queue import Queue
import time


@dataclass
class FileInfo:
    """Information sur un fichier - Optimisé pour M1"""
    path: str
    size: int
    hash_md5: Optional[str] = None
    modified_time: float = 0.0
    device_id: Optional[int] = None  # Pour optimiser les accès disque sur M1
    inode: Optional[int] = None      # Pour détecter les liens physiques
    file_type: str = "file"          # Type de fichier (image, video, symlink, etc.)
    is_removable: bool = True        # Si le fichier peut être supprimé
    
    def __post_init__(self):
        # Vérifier d'abord si c'est un lien symbolique
        if os.path.islink(self.path):
            self.file_type = "symlink"
            self.is_removable = self._is_removable()
            
            # Pour les liens symboliques, obtenir les infos du lien lui-même
            try:
                stat = os.lstat(self.path)  # lstat pour le lien, pas la cible
                self.size = stat.st_size
                self.modified_time = stat.st_mtime
                self.device_id = stat.st_dev
                self.inode = stat.st_ino
            except (OSError, IOError):
                pass
        elif os.path.exists(self.path):
            try:
                stat = os.stat(self.path)
                self.size = stat.st_size
                self.modified_time = stat.st_mtime
                self.device_id = stat.st_dev
                self.inode = stat.st_ino
                
                # Déterminer le type de fichier
                self.file_type = self._get_file_type()
                
                # Vérifier si le fichier peut être supprimé
                self.is_removable = self._is_removable()
                
            except (OSError, IOError):
                pass
    
    def _get_file_type(self) -> str:
        """Détermine le type du fichier"""
        import mimetypes
        
        if os.path.islink(self.path):
            return "symlink"
        
        mime_type, _ = mimetypes.guess_type(self.path)
        if mime_type:
            if mime_type.startswith('image/'):
                return "image"
            elif mime_type.startswith('video/'):
                return "video"
            elif mime_type.startswith('audio/'):
                return "audio"
        
        return "file"
    
    def _is_removable(self) -> bool:
        """Vérifie si le fichier peut être supprimé"""
        try:
            # Vérifier si c'est un lien symbolique brisé
            if os.path.islink(self.path):
                target = os.readlink(self.path)
                # Si le lien pointe vers un fichier qui n'existe pas
                if not os.path.exists(os.path.join(os.path.dirname(self.path), target)):
                    return False  # Lien brisé - ne pas supprimer automatiquement
            
            # Vérifier les permissions
            if not os.access(self.path, os.W_OK):
                return False
            
            # Vérifier si c'est un fichier système sur macOS
            if os.path.dirname(self.path).startswith(('/System', '/Library/System', '/usr/lib')):
                return False
                
            return True
        except (OSError, IOError):
            return False


class M1OptimizedDuplicateFinder:
    """Classe optimisée pour Apple M1 - Utilise tous les cœurs et la mémoire unifiée"""
    
    def __init__(self, max_workers: Optional[int] = None):
        # Optimisation M1: utiliser tous les cœurs de performance + efficience
        cpu_count = os.cpu_count() or 8
        self.max_workers = max_workers or min(cpu_count, 16)  # Limité à 16 pour éviter la sur-allocation
        
        # Détection si on est sur ARM64 (M1/M2)
        self.is_apple_silicon = platform.machine() in ('arm64', 'aarch64')
        
        # Taille de chunk optimisée pour M1 (plus grande grâce à la mémoire unifiée)
        self.chunk_size = 1024 * 1024 if self.is_apple_silicon else 64 * 1024  # 1MB vs 64KB
        
        # Cache pour éviter de recalculer les hash
        self.hash_cache: Dict[Tuple[int, float, int], str] = {}
        
        self.files_by_size: Dict[int, List[FileInfo]] = {}
        self.duplicates: List[List[FileInfo]] = []
    
    def _get_file_signature(self, file_info: FileInfo) -> Tuple[int, float, int]:
        """Crée une signature unique pour le cache des hash"""
        return (file_info.size, file_info.modified_time, file_info.inode or 0)
    
    def calculate_md5_optimized(self, file_path: str) -> str:
        """Calcule le hash MD5 optimisé pour M1 avec memory mapping"""
        try:
            with open(file_path, "rb") as f:
                # Pour les petits fichiers, lecture directe
                file_size = os.path.getsize(file_path)
                
                if file_size < 64 * 1024:  # < 64KB
                    return hashlib.md5(f.read()).hexdigest()
                
                # Pour les gros fichiers, utiliser memory mapping (plus efficace sur M1)
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    hash_md5 = hashlib.md5()
                    
                    # Traitement par chunks optimisés pour M1
                    for i in range(0, len(mm), self.chunk_size):
                        chunk = mm[i:i + self.chunk_size]
                        hash_md5.update(chunk)
                    
                    return hash_md5.hexdigest()
        except (OSError, IOError, ValueError):
            return ""
    
    def calculate_md5_batch(self, file_paths: List[str]) -> Dict[str, str]:
        """Calcule les hash MD5 en parallèle sur plusieurs cœurs M1"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumettre tous les calculs en parallèle
            future_to_path = {
                executor.submit(self.calculate_md5_optimized, path): path 
                for path in file_paths
            }
            
            # Récupérer les résultats au fur et à mesure
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    hash_result = future.result()
                    if hash_result:
                        results[path] = hash_result
                except Exception:
                    pass  # Ignorer les erreurs
        
        return results
    
    def scan_directory_optimized(self, directory: str, progress_callback=None) -> List[List[FileInfo]]:
        """Scanne un répertoire optimisé pour M1 - Parallélisation maximale"""
        self.files_by_size.clear()
        self.duplicates.clear()
        
        print(f"🚀 Scan optimisé M1 - Utilisation de {self.max_workers} workers")
        
        # Phase 1: Collecte rapide des fichiers avec parallélisation
        start_time = time.time()
        all_files = []
        
        def collect_files_worker(root_path: Path) -> List[FileInfo]:
            """Worker pour collecter les fichiers dans un thread"""
            files = []
            try:
                for file_path in root_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_info = FileInfo(str(file_path), 0)
                            if file_info.size > 0:  # Ignorer les fichiers vides
                                files.append(file_info)
                        except (OSError, IOError):
                            continue
            except (OSError, PermissionError):
                pass
            return files
        
        # Diviser le travail par sous-répertoires pour paralléliser
        root_path = Path(directory)
        subdirs = [root_path]
        
        # Ajouter les sous-répertoires de premier niveau pour paralléliser
        try:
            for item in root_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    subdirs.append(item)
        except (OSError, PermissionError):
            pass
        
        # Traitement parallèle de la collecte
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dir = {executor.submit(collect_files_worker, subdir): subdir for subdir in subdirs}
            
            for future in concurrent.futures.as_completed(future_to_dir):
                try:
                    files = future.result()
                    all_files.extend(files)
                    
                    if progress_callback and len(all_files) % 1000 == 0:
                        progress_callback(len(all_files), 0)
                        
                except Exception:
                    continue
        
        print(f"📁 {len(all_files)} fichiers collectés en {time.time() - start_time:.2f}s")
        
        # Phase 2: Groupement par taille (optimisé)
        for file_info in all_files:
            size = file_info.size
            if size not in self.files_by_size:
                self.files_by_size[size] = []
            self.files_by_size[size].append(file_info)
        
        # Phase 3: Calcul des hash en parallèle pour les candidats doublons
        candidate_groups = [files for files in self.files_by_size.values() if len(files) > 1]
        total_candidates = sum(len(group) for group in candidate_groups)
        
        print(f"🔍 {total_candidates} fichiers candidats à analyser en {len(candidate_groups)} groupes")
        
        processed = 0
        for group in candidate_groups:
            # Calculer les hash en parallèle pour ce groupe
            file_paths = [f.path for f in group]
            hash_results = self.calculate_md5_batch(file_paths)
            
            # Assigner les hash aux FileInfo
            for file_info in group:
                if file_info.path in hash_results:
                    file_info.hash_md5 = hash_results[file_info.path]
            
            # Grouper par hash
            files_by_hash: Dict[str, List[FileInfo]] = {}
            for file_info in group:
                if file_info.hash_md5:
                    hash_key = file_info.hash_md5
                    if hash_key not in files_by_hash:
                        files_by_hash[hash_key] = []
                    files_by_hash[hash_key].append(file_info)
            
            # Ajouter les groupes de doublons
            for hash_files in files_by_hash.values():
                if len(hash_files) > 1:
                    self.duplicates.append(hash_files)
            
            processed += len(group)
            if progress_callback:
                progress_callback(processed, total_candidates)
        
        scan_time = time.time() - start_time
        print(f"✅ Scan terminé en {scan_time:.2f}s - {len(self.duplicates)} groupes de doublons trouvés")
        
        return self.duplicates


# Garde la classe originale pour compatibilité
class DuplicateFinder(M1OptimizedDuplicateFinder):
    """Alias pour compatibilité - utilise automatiquement la version optimisée M1"""
    def __init__(self):
        super().__init__()
    
    def calculate_md5(self, file_path: str) -> str:
        """Méthode de compatibilité"""
        return self.calculate_md5_optimized(file_path)
    
    def scan_directory(self, directory: str, progress_callback=None) -> List[List[FileInfo]]:
        """Méthode de compatibilité - utilise la version optimisée"""
        return self.scan_directory_optimized(directory, progress_callback)


class M1OptimizedCacheCleaner:
    """Nettoyeur de cache optimisé pour Apple M1"""
    
    def __init__(self):
        # Optimisation M1: plus de workers pour l'I/O
        self.max_workers = min(os.cpu_count() or 8, 20)
        self.is_apple_silicon = platform.machine() in ('arm64', 'aarch64')
        self.cache_directories = self._get_cache_directories()
    
    def _get_cache_directories(self) -> List[str]:
        """Retourne les répertoires de cache selon l'OS - Optimisé M1"""
        system = platform.system()
        home = Path.home()
        cache_dirs = []
        
        if system == "Darwin":  # macOS - Optimisations spéciales M1
            cache_dirs.extend([
                str(home / "Library/Caches"),
                str(home / "Library/Application Support"),
                "/tmp",
                "/var/tmp",
                str(home / "Library/Logs"),
                str(home / "Library/Safari/LocalStorage"),
                str(home / "Library/Safari/Databases"),
                # Caches spécifiques M1/Apple Silicon
                str(home / "Library/Developer/Xcode/DerivedData"),
                str(home / "Library/Developer/CoreSimulator/Caches"),
                str(home / "Library/Caches/com.apple.dt.Xcode"),
                # Caches Rosetta 2 sur M1
                "/var/folders",  # Caches temporaires système
            ])
        elif system == "Linux":
            cache_dirs.extend([
                str(home / ".cache"),
                "/tmp",
                "/var/tmp",
                str(home / ".local/share/Trash"),
                str(home / ".mozilla/firefox/*/Cache"),
                str(home / ".config/google-chrome/Default/Cache"),
            ])
        elif system == "Windows":
            cache_dirs.extend([
                os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
                os.path.expandvars(r"%TEMP%"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Temporary Internet Files"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
                os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles\*\cache2"),
            ])
        
        return [d for d in cache_dirs if os.path.exists(d)]
    
    def _scan_cache_directory_worker(self, cache_dir: str) -> List[FileInfo]:
        """Worker pour scanner un répertoire de cache en parallèle"""
        cache_files = []
        try:
            for file_path in Path(cache_dir).rglob('*'):
                if file_path.is_file():
                    try:
                        file_info = FileInfo(str(file_path), 0)
                        # Filtrer les fichiers cache récents (< 1 jour) pour macOS M1
                        if self.is_apple_silicon:
                            age_hours = (time.time() - file_info.modified_time) / 3600
                            if age_hours < 24:  # Garde les caches récents
                                continue
                        cache_files.append(file_info)
                    except (OSError, IOError):
                        continue
        except (OSError, PermissionError):
            pass
        return cache_files
    
    def scan_cache_files_optimized(self, progress_callback=None) -> List[FileInfo]:
        """Scanne les fichiers de cache en parallèle - Optimisé M1"""
        print(f"🧹 Scan cache optimisé M1 - {len(self.cache_directories)} répertoires")
        
        all_cache_files = []
        
        # Traitement parallèle des répertoires de cache
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dir = {
                executor.submit(self._scan_cache_directory_worker, cache_dir): cache_dir 
                for cache_dir in self.cache_directories
            }
            
            for future in concurrent.futures.as_completed(future_to_dir):
                cache_dir = future_to_dir[future]
                try:
                    cache_files = future.result()
                    all_cache_files.extend(cache_files)
                    
                    if progress_callback:
                        progress_callback(len(all_cache_files))
                        
                    print(f"📂 {cache_dir}: {len(cache_files)} fichiers cache")
                except Exception as e:
                    print(f"⚠️  Erreur dans {cache_dir}: {e}")
        
        # Tri par taille décroissante pour faciliter le nettoyage
        all_cache_files.sort(key=lambda x: x.size, reverse=True)
        
        total_size = sum(f.size for f in all_cache_files)
        print(f"💾 Total cache: {len(all_cache_files)} fichiers, {total_size / (1024*1024):.1f} MB")
        
        return all_cache_files


# Classe de compatibilité
class CacheCleaner(M1OptimizedCacheCleaner):
    """Alias pour compatibilité - utilise automatiquement la version optimisée M1"""
    def scan_cache_files(self, progress_callback=None) -> List[FileInfo]:
        """Méthode de compatibilité"""
        return self.scan_cache_files_optimized(progress_callback)


class OrphanedFilesFinder:
    """Classe pour trouver les fichiers orphelins"""
    
    def __init__(self):
        self.application_dirs = self._get_application_directories()
        self.installed_apps = self._get_installed_applications()
    
    def _get_application_directories(self) -> List[str]:
        """Retourne les répertoires d'applications selon l'OS"""
        system = platform.system()
        home = Path.home()
        app_dirs = []
        
        if system == "Darwin":  # macOS
            app_dirs.extend([
                str(home / "Library/Application Support"),
                str(home / "Library/Preferences"),
                str(home / "Library/Logs"),
                "/Applications",
                str(home / "Applications"),
            ])
        elif system == "Linux":
            app_dirs.extend([
                str(home / ".config"),
                str(home / ".local/share"),
                "/usr/share/applications",
                str(home / ".local/share/applications"),
            ])
        elif system == "Windows":
            app_dirs.extend([
                os.path.expandvars(r"%APPDATA%"),
                os.path.expandvars(r"%LOCALAPPDATA%"),
                os.path.expandvars(r"%PROGRAMFILES%"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%"),
            ])
        
        return [d for d in app_dirs if os.path.exists(d)]
    
    def _get_installed_applications(self) -> List[str]:
        """Retourne la liste des applications installées"""
        apps = []
        system = platform.system()
        
        if system == "Darwin":  # macOS
            apps_dir = Path("/Applications")
            if apps_dir.exists():
                for app in apps_dir.iterdir():
                    if app.suffix == ".app":
                        apps.append(app.stem)
        
        # Ajouter d'autres méthodes selon l'OS
        return apps
    
    def find_orphaned_files(self, progress_callback=None) -> List[FileInfo]:
        """Trouve les fichiers orphelins"""
        orphaned_files = []
        
        for app_dir in self.application_dirs:
            try:
                for file_path in Path(app_dir).rglob('*'):
                    if file_path.is_file():
                        # Logique pour déterminer si le fichier est orphelin
                        # (simplifié pour cet exemple)
                        file_info = FileInfo(str(file_path), 0)
                        
                        # Vérifier si le fichier appartient à une app désinstallée
                        if self._is_orphaned(file_info):
                            orphaned_files.append(file_info)
                        
                        if progress_callback and len(orphaned_files) % 50 == 0:
                            progress_callback(len(orphaned_files))
            
            except (OSError, PermissionError):
                continue
        
        return orphaned_files
    
    def _is_orphaned(self, file_info: FileInfo) -> bool:
        """Détermine si un fichier est orphelin (logique simplifiée)"""
        # Ici on pourrait implémenter une logique plus sophistiquée
        # Pour l'instant, on considère les fichiers de plus de 30 jours 
        # dans certains répertoires comme potentiellement orphelins
        import time
        
        path = Path(file_info.path)
        current_time = time.time()
        
        # Fichiers de plus de 30 jours dans les logs
        if "log" in str(path).lower() or "Log" in str(path):
            return (current_time - file_info.modified_time) > (30 * 24 * 3600)
        
        return False


class M1OptimizedLargeFilesFinder:
    """Chercheur de gros fichiers optimisé pour Apple M1"""
    
    def __init__(self, min_size_mb: int = 100):
        self.min_size_bytes = min_size_mb * 1024 * 1024
        self.max_workers = min(os.cpu_count() or 8, 16)
        self.is_apple_silicon = platform.machine() in ('arm64', 'aarch64')
        
        # Optimisation M1: exclusions intelligentes
        self.excluded_dirs = {
            # macOS spécifique
            '/System', '/Library/Developer', '/usr/local/Cellar',
            '/.Spotlight-V100', '/.fseventsd', '/.Trashes',
            # Génériques
            '/.git', '/node_modules', '__pycache__', '.venv'
        }
    
    def _should_skip_directory(self, dir_path: Path) -> bool:
        """Détermine si un répertoire doit être ignoré - Optimisé M1"""
        dir_str = str(dir_path)
        
        # Exclusions spéciales pour M1/macOS
        if self.is_apple_silicon:
            if any(exclude in dir_str for exclude in [
                '/System/', '/Library/Developer/', '/private/var/vm/',
                'com.apple.', '.Spotlight-V100', '.fseventsd'
            ]):
                return True
        
        # Exclusions générales
        return any(exclude in dir_str for exclude in self.excluded_dirs)
    
    def _scan_directory_worker(self, directory: Path) -> List[FileInfo]:
        """Worker pour scanner un répertoire en parallèle"""
        large_files = []
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        # Vérification rapide de la taille sans FileInfo complet
                        size = file_path.stat().st_size
                        if size >= self.min_size_bytes:
                            file_info = FileInfo(str(file_path), size)
                            large_files.append(file_info)
                    except (OSError, IOError):
                        continue
                elif file_path.is_dir() and self._should_skip_directory(file_path):
                    continue
        except (OSError, PermissionError):
            pass
        
        return large_files
    
    def find_large_files_optimized(self, directory: str, progress_callback=None) -> List[FileInfo]:
        """Trouve les gros fichiers en parallèle - Optimisé M1"""
        print(f"🔍 Recherche gros fichiers optimisée M1 (≥{self.min_size_bytes/(1024*1024):.0f}MB)")
        
        root_path = Path(directory)
        all_large_files = []
        
        # Découper le travail par sous-répertoires pour paralléliser
        subdirs = [root_path]
        
        try:
            # Ajouter les sous-répertoires de premier niveau
            for item in root_path.iterdir():
                if item.is_dir() and not self._should_skip_directory(item):
                    subdirs.append(item)
        except (OSError, PermissionError):
            pass
        
        print(f"📁 Scan de {len(subdirs)} répertoires en parallèle")
        
        # Traitement parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dir = {
                executor.submit(self._scan_directory_worker, subdir): subdir 
                for subdir in subdirs
            }
            
            for future in concurrent.futures.as_completed(future_to_dir):
                subdir = future_to_dir[future]
                try:
                    large_files = future.result()
                    all_large_files.extend(large_files)
                    
                    if progress_callback:
                        progress_callback(len(all_large_files))
                    
                    if large_files:
                        print(f"📂 {subdir}: {len(large_files)} gros fichiers")
                        
                except Exception as e:
                    print(f"⚠️  Erreur dans {subdir}: {e}")
        
        # Tri par taille décroissante avec optimisation M1
        all_large_files.sort(key=lambda x: x.size, reverse=True)
        
        total_size = sum(f.size for f in all_large_files)
        print(f"💾 {len(all_large_files)} gros fichiers trouvés, {total_size/(1024**3):.2f} GB total")
        
        return all_large_files


# Classe de compatibilité
class LargeFilesFinder(M1OptimizedLargeFilesFinder):
    """Alias pour compatibilité - utilise automatiquement la version optimisée M1"""
    def find_large_files(self, directory: str, progress_callback=None) -> List[FileInfo]:
        """Méthode de compatibilité"""
        return self.find_large_files_optimized(directory, progress_callback)
