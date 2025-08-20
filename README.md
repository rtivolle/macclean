# MacClean - Nettoyeur de Stockage Multiplateforme

MacClean est une application GUI moderne et intuitive pour nettoyer le stockage de votre ordinateur. Elle vous aide à libérer de l'espace disque en identifiant et supprimant les fichiers en double, les caches inutiles, les fichiers orphelins et les gros fichiers.

## 🚀 Fonctionnalités

### 🔍 Détection de Doublons
- Identification précise des fichiers identiques par hash MD5 et taille
- Interface graphique pour sélectionner quels doublons supprimer
- Scan personnalisable par répertoire

### 🧹 Nettoyage de Cache
- Détection automatique des répertoires de cache selon l'OS
- Support des caches de navigateurs (Chrome, Firefox, Safari)
- Nettoyage des caches système et applications

### 👻 Fichiers Orphelins
- Identification des fichiers liés à des programmes désinstallés
- Détection des configurations et logs obsolètes
- Nettoyage sécurisé des résidus d'applications

### 📊 Gros Fichiers
- Recherche des fichiers volumineux
- Tri par taille décroissante
- Taille minimale configurable

### 📤 Export et Rapports
- Export des résultats en JSON, CSV ou TXT
- Rapports détaillés des opérations de nettoyage
- Informations système intégrées

## 🖥️ Compatibilité

- **macOS** 10.14+
- **Windows** 10+
- **Linux** (Ubuntu 18.04+, autres distributions)

## 📋 Prérequis

- Python 3.8+
- PySide6 (interface graphique)
- psutil (informations système)

## 🛠️ Installation

### Installation via pip (recommandé)

```bash
# Cloner le repository
git clone https://github.com/votre-username/macclean.git
cd macclean

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur macOS/Linux:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Installation pour le développement

```bash
# Installer les dépendances de développement
pip install -r requirements.txt
pip install pytest pytest-qt

# Lancer les tests
pytest tests/
```

## 🚀 Utilisation

### Lancement de l'application

```bash
python main.py
```

### Interface Utilisateur

L'application s'organise en 4 onglets principaux :

#### 1. Onglet Doublons
- Cliquez sur **"Parcourir"** pour sélectionner un répertoire
- Cliquez sur **"Scanner"** pour lancer la recherche
- Cochez les fichiers à supprimer dans la liste
- Cliquez sur **"Supprimer sélectionnés"** pour confirmer

#### 2. Onglet Cache
- Cliquez sur **"Scanner le cache"** pour analyser automatiquement
- Sélectionnez les fichiers cache à supprimer
- Confirmez la suppression

#### 3. Onglet Fichiers Orphelins
- Lancez le scan pour identifier les fichiers orphelins
- Examinez la liste avant suppression
- Supprimez les fichiers non nécessaires

#### 4. Onglet Gros Fichiers
- Configurez la taille minimale (en MB)
- Sélectionnez le répertoire à scanner
- Triez et supprimez les fichiers volumineux

### Fonctionnalités Avancées

#### Export des Résultats
1. Sélectionnez l'onglet contenant les données à exporter
2. Cliquez sur **"Exporter"** dans la barre d'outils
3. Choisissez le format (JSON, CSV, TXT)
4. Sauvegardez le rapport

#### Options de Sélection
- **"Tout sélectionner"** : Coche tous les fichiers
- **"Tout désélectionner"** : Décoche tous les fichiers
- Sélection manuelle par clic sur les cases

## 🏗️ Architecture du Code

```
macclean/
├── main.py                 # Point d'entrée principal
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
├── src/
│   └── macclean/
│       ├── __init__.py
│       ├── core/          # Logique métier
│       │   ├── __init__.py
│       │   └── cleaner.py # Classes de nettoyage
│       ├── gui/           # Interface graphique
│       │   ├── __init__.py
│       │   └── main_window.py
│       └── utils/         # Utilitaires
│           ├── __init__.py
│           └── helpers.py
└── tests/                 # Tests unitaires
    ├── conftest.py
    ├── test_init.py
    ├── test_core.py
    └── test_gui.py
```

### Modules Principaux

#### `macclean.core.cleaner`
- `DuplicateFinder`: Détection de doublons
- `CacheCleaner`: Nettoyage de cache
- `OrphanedFilesFinder`: Recherche de fichiers orphelins
- `LargeFilesFinder`: Identification de gros fichiers
- `FileInfo`: Structure de données pour les fichiers

#### `macclean.gui.main_window`
- `MacCleanApp`: Fenêtre principale
- `FileTableWidget`: Widget de table personnalisé
- `ScanWorker`: Worker thread pour les scans

#### `macclean.utils.helpers`
- Fonctions d'export (JSON, CSV, TXT)
- Formatage de taille de fichiers
- Suppression sécurisée
- Informations système

## 🧪 Tests

### Lancement des tests

```bash
# Tests complets
pytest tests/ -v

# Tests spécifiques
pytest tests/test_core.py -v
pytest tests/test_gui.py -v

# Tests avec couverture
pytest tests/ --cov=src/macclean --cov-report=html
```

### Structure des Tests

- **test_core.py**: Tests des fonctionnalités de nettoyage
- **test_gui.py**: Tests de l'interface graphique
- **test_init.py**: Tests d'initialisation du package

## 🔧 Configuration

### Variables d'Environnement

```bash
# Pour les tests GUI en mode headless
export QT_QPA_PLATFORM=offscreen
```

### Paramètres Personnalisables

- Taille minimale pour les "gros fichiers" (par défaut: 100 MB)
- Répertoires de scan personnalisés
- Formats d'export

## 🐛 Dépannage

### Problèmes Courants

#### ImportError: No module named 'PySide6'
```bash
pip install PySide6
```

#### Erreur de permissions sur macOS/Linux
```bash
# Lancer avec sudo si nécessaire pour accéder aux répertoires système
sudo python main.py
```

#### L'application ne se lance pas
1. Vérifiez Python 3.8+
2. Vérifiez l'installation des dépendances
3. Activez l'environnement virtuel

### Logs et Debug

L'application affiche les erreurs dans la console. Pour plus de détails :

```bash
# Mode debug
python main.py --debug
```

## 🤝 Contribution

### Comment Contribuer

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commitez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

### Standards de Code

- Code Python suivant PEP 8
- Documentation des fonctions publiques
- Tests unitaires pour les nouvelles fonctionnalités
- Messages de commit descriptifs

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ✨ Fonctionnalités à Venir

- [ ] Mode dark/light
- [ ] Planification automatique du nettoyage
- [ ] Filtres avancés (par extension, date)
- [ ] Restauration depuis la corbeille
- [ ] Support de plus de langues
- [ ] Interface en ligne de commande
- [ ] Notifications système

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/votre-username/macclean/issues)
- **Documentation**: [Wiki](https://github.com/votre-username/macclean/wiki)
- **Email**: support@macclean.app

## 📊 Statistiques

- **Langages**: Python 100%
- **Interface**: PySide6 (Qt)
- **Tests**: pytest
- **Couverture**: 90%+

---

**MacClean** - Libérez l'espace, optimisez les performances ! 🚀
