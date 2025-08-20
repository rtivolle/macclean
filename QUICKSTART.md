# MacClean - Guide de Démarrage Rapide

## Installation Express

```bash
# 1. Cloner et installer
git clone <votre-repo>
cd macclean
./start.sh --install

# 2. Lancer l'application
./start.sh
```

## Usage Rapide

### Interface Graphique
```bash
python main.py
```

### Démo CLI (Test des fonctionnalités)
```bash
python demo_cli.py
```

### Tests
```bash
./start.sh --test
```

## Structure du Projet

```
macclean/
├── main.py              # Point d'entrée GUI
├── demo_cli.py          # Démo/Test CLI  
├── start.sh / start.bat # Scripts de démarrage
├── requirements.txt     # Dépendances
├── pyproject.toml       # Configuration
├── src/macclean/        # Code source
│   ├── core/           # Logique métier
│   ├── gui/            # Interface graphique
│   └── utils/          # Utilitaires
└── tests/              # Tests unitaires
```

## Fonctionnalités Principales

✅ **Doublons**: Détection par hash MD5 + taille  
✅ **Cache**: Nettoyage automatique multi-OS  
✅ **Orphelins**: Fichiers de programmes désinstallés  
✅ **Gros fichiers**: Recherche par taille configurable  
✅ **Export**: JSON, CSV, TXT  
✅ **Tests**: 20+ tests unitaires  
✅ **Multiplateforme**: Windows, macOS, Linux  

## Compatibilité

- **Python**: 3.8+
- **Interface**: PySide6 (Qt)
- **OS**: Windows 10+, macOS 10.14+, Linux Ubuntu 18.04+

## Support

- Tests: `pytest tests/ -v`
- Logs: Console intégrée
- Debug: `python main.py --debug` (si implémenté)

---

**MacClean** - Libérez l'espace, optimisez les performances ! 🚀
