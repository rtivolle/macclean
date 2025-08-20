"""
Fenêtre principale de l'application MacClean
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QCheckBox, QProgressBar, 
    QFileDialog, QMessageBox, QHeaderView, QGroupBox,
    QSpinBox, QComboBox, QTextEdit, QSplitter,
    QStatusBar, QMenuBar, QMenu, QToolBar
)
from PySide6.QtCore import (
    Qt, QThread, QObject, Signal, QTimer, QSettings
)
from PySide6.QtGui import QAction, QIcon, QFont, QPalette

from macclean.core import (
    DuplicateFinder, CacheCleaner, OrphanedFilesFinder, 
    LargeFilesFinder, FileInfo
)
from macclean.utils import (
    format_file_size, safe_delete_file, export_to_json,
    export_to_csv, export_to_txt, get_system_info
)


class ScanWorker(QObject):
    """Worker thread pour les opérations de scan"""
    
    progress = Signal(int, int)  # current, total
    finished = Signal(object)    # results
    error = Signal(str)         # error message
    
    def __init__(self, scan_type: str, parameters: dict):
        super().__init__()
        self.scan_type = scan_type
        self.parameters = parameters
        self.should_stop = False
    
    def run(self):
        """Exécute le scan"""
        try:
            results = []
            
            if self.scan_type == "duplicates":
                finder = DuplicateFinder()
                directory = self.parameters.get("directory", str(Path.home()))
                duplicates = finder.scan_directory(
                    directory, 
                    progress_callback=self._progress_callback
                )
                # Aplatir la liste des groupes de doublons
                for group in duplicates:
                    results.extend(group)
            
            elif self.scan_type == "cache":
                cleaner = CacheCleaner()
                results = cleaner.scan_cache_files(
                    progress_callback=self._cache_progress_callback
                )
            
            elif self.scan_type == "orphans":
                finder = OrphanedFilesFinder()
                results = finder.find_orphaned_files(
                    progress_callback=self._orphan_progress_callback
                )
            
            elif self.scan_type == "large":
                finder = LargeFilesFinder(
                    min_size_mb=self.parameters.get("min_size_mb", 100)
                )
                directory = self.parameters.get("directory", str(Path.home()))
                results = finder.find_large_files(
                    directory,
                    progress_callback=self._large_progress_callback
                )
            
            self.finished.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))
    
    def _progress_callback(self, current: int, total: int):
        """Callback pour le progrès des doublons"""
        if not self.should_stop:
            self.progress.emit(current, total)
    
    def _cache_progress_callback(self, count: int):
        """Callback pour le progrès du cache"""
        if not self.should_stop:
            self.progress.emit(count, 0)
    
    def _orphan_progress_callback(self, count: int):
        """Callback pour le progrès des orphelins"""
        if not self.should_stop:
            self.progress.emit(count, 0)
    
    def _large_progress_callback(self, count: int):
        """Callback pour le progrès des gros fichiers"""
        if not self.should_stop:
            self.progress.emit(count, 0)
    
    def stop(self):
        """Arrête le scan"""
        self.should_stop = True


class FileTableWidget(QTableWidget):
    """Widget de table personnalisé pour afficher les fichiers"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.files_data: List[FileInfo] = []
    
    def setup_table(self):
        """Configure la table"""
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Sélection", "Nom", "Taille", "Chemin", "Date modif."
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Taille
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Chemin
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Date
        
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
    
    def populate_table(self, files: List[FileInfo]):
        """Remplit la table avec les fichiers"""
        self.files_data = files
        self.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            # Checkbox
            checkbox = QCheckBox()
            self.setCellWidget(row, 0, checkbox)
            
            # Nom du fichier
            filename = os.path.basename(file_info.path)
            self.setItem(row, 1, QTableWidgetItem(filename))
            
            # Taille
            size_item = QTableWidgetItem(format_file_size(file_info.size))
            size_item.setData(Qt.UserRole, file_info.size)  # Pour le tri
            self.setItem(row, 2, size_item)
            
            # Chemin
            self.setItem(row, 3, QTableWidgetItem(file_info.path))
            
            # Date de modification
            import datetime
            date_str = datetime.datetime.fromtimestamp(
                file_info.modified_time
            ).strftime("%Y-%m-%d %H:%M")
            self.setItem(row, 4, QTableWidgetItem(date_str))
    
    def get_selected_files(self) -> List[FileInfo]:
        """Retourne les fichiers sélectionnés"""
        selected_files = []
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_files.append(self.files_data[row])
        return selected_files
    
    def select_all(self, checked: bool):
        """Sélectionne/désélectionne tous les fichiers"""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)


class MacCleanApp(QMainWindow):
    """Fenêtre principale de l'application MacClean"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MacClean", "MacClean")
        self.setup_ui()
        self.setup_connections()
        self.current_worker: Optional[ScanWorker] = None
        self.current_thread: Optional[QThread] = None
        
        # Charger les paramètres
        self.load_settings()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("MacClean - Nettoyeur de stockage")
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre d'outils
        self.create_toolbar()
        
        # Informations système
        self.create_system_info()
        main_layout.addWidget(self.system_info_group)
        
        # Onglets principaux
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Onglet Doublons
        self.create_duplicates_tab()
        
        # Onglet Cache
        self.create_cache_tab()
        
        # Onglet Fichiers orphelins
        self.create_orphans_tab()
        
        # Onglet Gros fichiers
        self.create_large_files_tab()
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Action Rafraîchir
        refresh_action = QAction("Rafraîchir", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Action Exporter
        export_action = QAction("Exporter", self)
        export_action.triggered.connect(self.export_results)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Action À propos
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
    
    def create_system_info(self):
        """Crée le widget d'informations système"""
        self.system_info_group = QGroupBox("Informations système")
        layout = QHBoxLayout(self.system_info_group)
        
        # Récupérer les infos système
        sys_info = get_system_info()
        
        # Plateforme
        platform_label = QLabel(f"Système: {sys_info['platform']}")
        layout.addWidget(platform_label)
        
        # Espace disque
        disk_label = QLabel(
            f"Disque: {format_file_size(sys_info['disk_used'])} / "
            f"{format_file_size(sys_info['disk_total'])} "
            f"({sys_info['disk_percent']:.1f}%)"
        )
        layout.addWidget(disk_label)
        
        layout.addStretch()
    
    def create_duplicates_tab(self):
        """Crée l'onglet des doublons"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        
        # Sélection du répertoire
        self.duplicate_dir_label = QLabel("Répertoire: " + str(Path.home()))
        controls_layout.addWidget(self.duplicate_dir_label)
        
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self.browse_duplicate_directory)
        controls_layout.addWidget(browse_btn)
        
        scan_btn = QPushButton("Scanner")
        scan_btn.clicked.connect(self.scan_duplicates)
        controls_layout.addWidget(scan_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Table des résultats
        self.duplicates_table = FileTableWidget()
        layout.addWidget(self.duplicates_table)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(
            lambda: self.duplicates_table.select_all(True)
        )
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tout désélectionner")
        deselect_all_btn.clicked.connect(
            lambda: self.duplicates_table.select_all(False)
        )
        actions_layout.addWidget(deselect_all_btn)
        
        actions_layout.addStretch()
        
        delete_btn = QPushButton("Supprimer sélectionnés")
        delete_btn.clicked.connect(
            lambda: self.delete_selected_files(self.duplicates_table)
        )
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        self.tabs.addTab(tab_widget, "Doublons")
    
    def create_cache_tab(self):
        """Crée l'onglet du cache"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        
        scan_btn = QPushButton("Scanner le cache")
        scan_btn.clicked.connect(self.scan_cache)
        controls_layout.addWidget(scan_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Table des résultats
        self.cache_table = FileTableWidget()
        layout.addWidget(self.cache_table)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(
            lambda: self.cache_table.select_all(True)
        )
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tout désélectionner")
        deselect_all_btn.clicked.connect(
            lambda: self.cache_table.select_all(False)
        )
        actions_layout.addWidget(deselect_all_btn)
        
        actions_layout.addStretch()
        
        delete_btn = QPushButton("Supprimer sélectionnés")
        delete_btn.clicked.connect(
            lambda: self.delete_selected_files(self.cache_table)
        )
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        self.tabs.addTab(tab_widget, "Cache")
    
    def create_orphans_tab(self):
        """Crée l'onglet des fichiers orphelins"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        
        scan_btn = QPushButton("Scanner les fichiers orphelins")
        scan_btn.clicked.connect(self.scan_orphans)
        controls_layout.addWidget(scan_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Table des résultats
        self.orphans_table = FileTableWidget()
        layout.addWidget(self.orphans_table)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(
            lambda: self.orphans_table.select_all(True)
        )
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tout désélectionner")
        deselect_all_btn.clicked.connect(
            lambda: self.orphans_table.select_all(False)
        )
        actions_layout.addWidget(deselect_all_btn)
        
        actions_layout.addStretch()
        
        delete_btn = QPushButton("Supprimer sélectionnés")
        delete_btn.clicked.connect(
            lambda: self.delete_selected_files(self.orphans_table)
        )
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        self.tabs.addTab(tab_widget, "Fichiers orphelins")
    
    def create_large_files_tab(self):
        """Crée l'onglet des gros fichiers"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        
        # Sélection du répertoire
        self.large_files_dir_label = QLabel("Répertoire: " + str(Path.home()))
        controls_layout.addWidget(self.large_files_dir_label)
        
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self.browse_large_files_directory)
        controls_layout.addWidget(browse_btn)
        
        # Taille minimale
        controls_layout.addWidget(QLabel("Taille min (MB):"))
        self.min_size_spinbox = QSpinBox()
        self.min_size_spinbox.setRange(1, 10000)
        self.min_size_spinbox.setValue(100)
        controls_layout.addWidget(self.min_size_spinbox)
        
        scan_btn = QPushButton("Scanner")
        scan_btn.clicked.connect(self.scan_large_files)
        controls_layout.addWidget(scan_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Table des résultats
        self.large_files_table = FileTableWidget()
        layout.addWidget(self.large_files_table)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(
            lambda: self.large_files_table.select_all(True)
        )
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tout désélectionner")
        deselect_all_btn.clicked.connect(
            lambda: self.large_files_table.select_all(False)
        )
        actions_layout.addWidget(deselect_all_btn)
        
        actions_layout.addStretch()
        
        delete_btn = QPushButton("Supprimer sélectionnés")
        delete_btn.clicked.connect(
            lambda: self.delete_selected_files(self.large_files_table)
        )
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        self.tabs.addTab(tab_widget, "Gros fichiers")
    
    def setup_connections(self):
        """Configure les connexions des signaux"""
        pass
    
    def browse_duplicate_directory(self):
        """Ouvre le dialogue de sélection de répertoire pour les doublons"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner le répertoire à scanner"
        )
        if directory:
            self.duplicate_dir_label.setText(f"Répertoire: {directory}")
    
    def browse_large_files_directory(self):
        """Ouvre le dialogue de sélection de répertoire pour les gros fichiers"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner le répertoire à scanner"
        )
        if directory:
            self.large_files_dir_label.setText(f"Répertoire: {directory}")
    
    def scan_duplicates(self):
        """Lance le scan des doublons"""
        directory = self.duplicate_dir_label.text().replace("Répertoire: ", "")
        self.start_scan("duplicates", {"directory": directory})
    
    def scan_cache(self):
        """Lance le scan du cache"""
        self.start_scan("cache", {})
    
    def scan_orphans(self):
        """Lance le scan des fichiers orphelins"""
        self.start_scan("orphans", {})
    
    def scan_large_files(self):
        """Lance le scan des gros fichiers"""
        directory = self.large_files_dir_label.text().replace("Répertoire: ", "")
        min_size = self.min_size_spinbox.value()
        self.start_scan("large", {"directory": directory, "min_size_mb": min_size})
    
    def start_scan(self, scan_type: str, parameters: dict):
        """Démarre un scan en arrière-plan"""
        if self.current_thread and self.current_thread.isRunning():
            QMessageBox.warning(self, "Scan en cours", "Un scan est déjà en cours.")
            return
        
        # Créer le worker et le thread
        self.current_worker = ScanWorker(scan_type, parameters)
        self.current_thread = QThread()
        
        # Déplacer le worker vers le thread
        self.current_worker.moveToThread(self.current_thread)
        
        # Connecter les signaux
        self.current_thread.started.connect(self.current_worker.run)
        self.current_worker.progress.connect(self.update_progress)
        self.current_worker.finished.connect(self.scan_finished)
        self.current_worker.error.connect(self.scan_error)
        self.current_worker.finished.connect(self.current_thread.quit)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        self.current_thread.finished.connect(self.current_thread.deleteLater)
        
        # Démarrer le scan
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Scan en cours: {scan_type}")
        self.current_thread.start()
    
    def update_progress(self, current: int, total: int):
        """Met à jour la barre de progression"""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        else:
            # Mode indéterminé
            self.progress_bar.setMaximum(0)
            self.progress_bar.setValue(0)
    
    def scan_finished(self, results: List[FileInfo]):
        """Appelé quand le scan est terminé"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Scan terminé. {len(results)} fichiers trouvés.")
        
        # Mettre à jour la table correspondante
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # Doublons
            self.duplicates_table.populate_table(results)
        elif current_tab == 1:  # Cache
            self.cache_table.populate_table(results)
        elif current_tab == 2:  # Orphelins
            self.orphans_table.populate_table(results)
        elif current_tab == 3:  # Gros fichiers
            self.large_files_table.populate_table(results)
    
    def scan_error(self, error_message: str):
        """Appelé en cas d'erreur de scan"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Erreur de scan")
        QMessageBox.critical(self, "Erreur", f"Erreur lors du scan: {error_message}")
    
    def delete_selected_files(self, table: FileTableWidget):
        """Supprime les fichiers sélectionnés"""
        selected_files = table.get_selected_files()
        
        if not selected_files:
            QMessageBox.information(self, "Aucune sélection", "Aucun fichier sélectionné.")
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer {len(selected_files)} fichier(s) ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            successful_deletions = 0
            
            for file_info in selected_files:
                if safe_delete_file(file_info.path):
                    successful_deletions += 1
            
            QMessageBox.information(
                self, "Suppression terminée",
                f"{successful_deletions}/{len(selected_files)} fichier(s) supprimé(s)."
            )
            
            # Rafraîchir la table
            self.refresh_current_tab()
    
    def refresh_current_tab(self):
        """Rafraîchit l'onglet actuel"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # Doublons
            self.scan_duplicates()
        elif current_tab == 1:  # Cache
            self.scan_cache()
        elif current_tab == 2:  # Orphelins
            self.scan_orphans()
        elif current_tab == 3:  # Gros fichiers
            self.scan_large_files()
    
    def export_results(self):
        """Exporte les résultats de l'onglet actuel"""
        current_tab = self.tabs.currentIndex()
        
        # Déterminer quelle table utiliser
        if current_tab == 0:
            table = self.duplicates_table
            tab_name = "doublons"
        elif current_tab == 1:
            table = self.cache_table
            tab_name = "cache"
        elif current_tab == 2:
            table = self.orphans_table
            tab_name = "orphelins"
        elif current_tab == 3:
            table = self.large_files_table
            tab_name = "gros_fichiers"
        else:
            return
        
        if not table.files_data:
            QMessageBox.information(self, "Aucune donnée", "Aucune donnée à exporter.")
            return
        
        # Sélectionner le format d'export
        formats = {
            "JSON (*.json)": "json",
            "CSV (*.csv)": "csv", 
            "Texte (*.txt)": "txt"
        }
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Exporter les résultats",
            f"macclean_{tab_name}",
            ";;".join(formats.keys())
        )
        
        if file_path:
            format_type = formats[selected_filter]
            
            success = False
            if format_type == "json":
                success = export_to_json(table.files_data, file_path)
            elif format_type == "csv":
                success = export_to_csv(table.files_data, file_path)
            elif format_type == "txt":
                success = export_to_txt(table.files_data, file_path)
            
            if success:
                QMessageBox.information(self, "Export réussi", f"Données exportées vers {file_path}")
            else:
                QMessageBox.critical(self, "Erreur d'export", "Échec de l'export des données.")
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self, "À propos de MacClean",
            "MacClean v1.0.0\n\n"
            "Application de nettoyage de stockage\n"
            "Multiplateforme (Windows, macOS, Linux)\n\n"
            "Fonctionnalités:\n"
            "• Détection de fichiers en double\n"
            "• Nettoyage de cache\n"
            "• Recherche de fichiers orphelins\n"
            "• Identification des gros fichiers\n\n"
            "Développé avec Python et PySide6"
        )
    
    def load_settings(self):
        """Charge les paramètres de l'application"""
        # Restaurer la géométrie de la fenêtre
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restaurer l'état de la fenêtre
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def save_settings(self):
        """Sauvegarde les paramètres de l'application"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """Gestionnaire de fermeture de l'application"""
        # Arrêter les scans en cours
        if self.current_worker:
            self.current_worker.stop()
        
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.quit()
            self.current_thread.wait()
        
        # Sauvegarder les paramètres
        self.save_settings()
        
        event.accept()
