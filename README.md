# Middleware de Collecte et de Stockage des Données - Projet e-ID

## Vue d'ensemble

Ce middleware permet la collecte, la validation, la transformation et le stockage automatisé des fichiers CSV provenant des modules IDPS, ABIS et ADJUDICATION du projet e-ID. Les données sont centralisées dans des bases de données PostgreSQL pour alimenter le pipeline BI.

## Architecture

Le middleware repose sur trois composants principaux :

1. **Dossier partagé** : Espace accessible pour déposer les fichiers CSV (dépot quotidien à partir de 02h00)
2. **CSV Handler** : Script Python pour le traitement des fichiers CSV et la persistance en base de données (exécution planifiée à 03h00)
3. **Base de données PostgreSQL** : Tables structurées pour conserver les événements (IDPS, ABIS, ADJUDICATION)

## Structure du Projet

```
Biometrics_BI/
├── middleware/              # Modules du middleware
│   ├── __init__.py
│   ├── config/               # Configuration centralisée
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models.py            # Modèles de données (DTOs/Entities)
│   ├── exceptions.py        # Exceptions personnalisées
│   ├── interfaces.py        # Interfaces (abstractions)
│   ├── factories.py         # Factories pour l'instanciation
│   ├── csv_handler.py       # Point d'entrée principal
│   ├── domains/              # Domaines (Architecture DDD)
│   │   ├── __init__.py
│   │   ├── registry.py      # Registry pour enregistrer les domaines
│   │   ├── bootstrap.py     # Bootstrap pour enregistrer tous les domaines
│   │   ├── base/            # Classes de base communes
│   │   │   └── domain_interface.py
│   │   ├── idps/            # Domaine IDPS
│   │   │   ├── domain.py
│   │   │   ├── file_pattern.py
│   │   │   ├── file_detector.py
│   │   │   ├── validator.py
│   │   │   ├── transformer.py
│   │   │   └── repository.py
│   │   ├── abis/            # Domaine ABIS
│   │   │   └── ... (même structure)
│   │   └── adjudication/   # Domaine ADJUDICATION
│   │       └── ... (même structure)
│   ├── services/            # Services (logique métier)
│   │   ├── __init__.py
│   │   ├── file_detection_service.py
│   │   ├── file_validation_service.py
│   │   ├── data_transformation_service.py
│   │   ├── ingestion_service.py
│   │   └── domain_ingestion_service.py  # Service basé sur DDD
│   ├── repositories/        # Repositories (accès aux données)
│   │   ├── __init__.py
│   │   ├── database_repository.py
│   │   └── file_archive_repository.py
│   └── utils/               # Utilitaires
│       ├── __init__.py
│       └── logger.py
├── database/                # Schémas de base de données
│   ├── schemas/
│   │   ├── idps_schema.sql
│   │   ├── abis_schema.sql
│   │   └── adjudication_schema.sql
│   └── init_databases.sh    # Script d'initialisation
├── input/                   # Répertoire d'entrée (fichiers CSV)
├── output/                  # Répertoire de sortie
├── archive/                 # Répertoire d'archivage
├── error/                   # Répertoire d'erreurs
├── logs/                    # Fichiers de logs
├── config.py                # Configuration (legacy - à migrer)
├── scheduler.py             # Scheduler pour exécution automatique
├── requirements.txt          # Dépendances Python
├── README.md                 # Documentation
└── ARCHITECTURE.md           # Documentation de l'architecture

```

## Processus d'Ingestion

Le pipeline d'ingestion suit les étapes suivantes :

1. **Détection** : Scan du répertoire partagé et identification des nouveaux fichiers
2. **Validation** : Vérification du format CSV, encodage, séparateur, entêtes et schéma
3. **Transformation** : Normalisation des données (dates, types, encodage), extraction JSON
4. **Chargement** : Insertion des données en base de données PostgreSQL
5. **Archivage** : Déplacement des fichiers traités vers le répertoire d'archive
6. **Gestion des erreurs** : Isolation des fichiers invalides et enregistrement des logs

## Installation

### Prérequis

- Python 3.8+
- PostgreSQL 12+
- Accès aux répertoires partagés (pour les fichiers CSV)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

1. Copier le fichier `.env.example` vers `.env` et configurer les variables d'environnement :

```bash
# Configuration des répertoires
INPUT_DIR=./input
ARCHIVE_DIR=./archive
ERROR_DIR=./error
LOGS_DIR=./logs

# Configuration Base de données IDPS
IDPS_DB_HOST=localhost
IDPS_DB_PORT=5432
IDPS_DB_NAME=idps_db
IDPS_DB_USER=postgres
IDPS_DB_PASSWORD=postgres

# Configuration Base de données ABIS
ABIS_DB_HOST=localhost
ABIS_DB_PORT=5432
ABIS_DB_NAME=abis_db
ABIS_DB_USER=postgres
ABIS_DB_PASSWORD=postgres

# Configuration Base de données ADJUDICATION
ADJUDICATION_DB_HOST=localhost
ADJUDICATION_DB_PORT=5432
ADJUDICATION_DB_NAME=adjudication_db
ADJUDICATION_DB_USER=postgres
ADJUDICATION_DB_PASSWORD=postgres

# Configuration Scheduler
SCHEDULER_START_TIME=03:00
SCAN_INTERVAL_MINUTES=60
```

### Initialisation de la base de données

Exécuter le script d'initialisation pour créer les bases de données et appliquer les schémas :

```bash
chmod +x database/init_databases.sh
./database/init_databases.sh
```

Ou manuellement avec psql :

```bash
psql -U postgres -f database/schemas/idps_schema.sql -d idps_db
psql -U postgres -f database/schemas/abis_schema.sql -d abis_db
psql -U postgres -f database/schemas/adjudication_schema.sql -d adjudication_db
```

## Utilisation

### Exécution manuelle

Pour traiter les fichiers CSV manuellement :

```bash
python -m middleware.csv_handler
```

### Exécution planifiée (Scheduler)

Pour lancer le scheduler qui exécutera automatiquement l'ingestion à l'heure configurée (par défaut 03h00) :

```bash
python scheduler.py
```

### Exécution via cron (Linux/Mac)

Ajouter une entrée dans le crontab :

```bash
0 3 * * * cd /chemin/vers/Biometrics_BI && /usr/bin/python3 -m middleware.csv_handler >> logs/cron.log 2>&1
```

### Exécution via Task Scheduler (Windows)

Créer une tâche planifiée qui exécute :

```
python.exe -m middleware.csv_handler
```

## Types de fichiers supportés

### Module IDPS

- **WO-BACKLOG** : Ordres de perso en backlog → Table `idps_workflow_events`
- **WO-FINISH** : Ordres de perso terminés → Table `idps_workflow_events`
- **QC-ERROR** : Erreurs de contrôle qualité → Table `idps_error_events`
- **PERSO-ERROR** : Erreurs de personnalisation → Table `idps_error_events`
- **SUP-ERROR** : Erreurs de supervision → Table `idps_error_events`

### Module ABIS

- Fichiers ABIS → Table `abis_events`

### Module ADJUDICATION

- Fichiers ADJUDICATION → Table `adjudication_events`

## Format des fichiers CSV

Les fichiers doivent suivre la nomenclature :
- **IDPS** : `IDPS-TG-EID-{TYPE}-{YYYY-MM-DD}.csv`
- Exemple : `IDPS-TG-EID-WO-BACKLOG-2025-11-11.csv`

## Architecture de la base de données

### Module IDPS

- **idps_workflow_events** : Suivi opérationnel des ordres de perso
- **idps_error_events** : Suivi des contrôles de qualité
- **idps_ingestion_audit_log** : Historique complet des traitements d'ingestion

### Module ABIS

- **abis_events** : Événements provenant de l'ABIS
- **abis_ingestion_audit_log** : Historique des traitements ABIS

### Module ADJUDICATION

- **adjudication_events** : Événements provenant de l'ADJUDICATION
- **adjudication_ingestion_audit_log** : Historique des traitements ADJUDICATION

## Logs et Monitoring

Les logs sont enregistrés dans le répertoire `logs/` avec un fichier par jour :
- Format : `csv_handler_YYYYMMDD.log`

Les logs d'audit sont stockés dans les tables `*_ingestion_audit_log` de chaque module.

## Gestion des erreurs

- Les fichiers invalides sont déplacés vers `error/YYYY-MM-DD/`
- Les erreurs sont enregistrées dans les tables d'audit avec le statut 'error'
- Les détails des erreurs sont disponibles dans le champ `error_message`

## Architecture

Ce projet utilise une **double architecture** :

### 1. Clean Code & SOLID Principles

- **Séparation des responsabilités** : Chaque composant a une seule responsabilité
- **Injection de dépendances** : Les composants dépendent d'interfaces, pas d'implémentations
- **Architecture en couches** : Domain, Application, Infrastructure
- **Code modulaire** : Facile à tester, maintenir et étendre

Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour plus de détails.

### 2. Domain-Driven Design (DDD)

- **Domaines indépendants** : Chaque module (IDPS, ABIS, ADJUDICATION) est un domaine séparé
- **Registry Pattern** : Chargement dynamique des domaines
- **Extensibilité** : Ajouter un nouveau module = créer un nouveau domaine
- **Isolation** : Chaque domaine a ses propres règles, validations et repositories

Voir [DDD_ARCHITECTURE.md](DDD_ARCHITECTURE.md) pour plus de détails sur l'architecture DDD.

### Structure des modules

Chaque module du middleware a une responsabilité spécifique :

- **FileDetectionService** : Détection et identification des fichiers
- **FileValidationService** : Validation du format et du contenu
- **DataTransformationService** : Transformation et normalisation
- **DatabaseRepository** : Gestion des opérations de base de données
- **FileArchiveRepository** : Archivage et organisation des fichiers
- **IngestionService** : Orchestration du processus complet
- **CSVHandler** : Point d'entrée principal

### Extension - Ajouter un Nouveau Domaine

Pour ajouter un nouveau module (domaine), suivez ces étapes :

1. **Créer la structure du domaine** :
   ```bash
   mkdir -p middleware/domains/new_module
   ```

2. **Créer les fichiers du domaine** :
   - `domain.py` : Classe principale du domaine
   - `file_pattern.py` : Pattern matching pour les fichiers
   - `file_detector.py` : Détection de fichiers
   - `validator.py` : Validation spécifique
   - `transformer.py` : Transformation spécifique
   - `repository.py` : Repository spécifique

3. **Enregistrer le domaine** dans `middleware/domains/bootstrap.py`

4. **Configurer la base de données** dans `.env` et `middleware/config/settings.py`

5. **Créer le schéma SQL** dans `database/schemas/new_module_schema.sql`

Voir [DDD_ARCHITECTURE.md](DDD_ARCHITECTURE.md) pour un guide détaillé.

## Stack de Technologie

- **Python 3.8+** : Langage de programmation
- **PostgreSQL** : Base de données relationnelle
- **psycopg2** : Driver PostgreSQL pour Python
- **pandas** : Traitement des données (optionnel, pour futures extensions)
- **schedule** : Bibliothèque de planification des tâches
- **chardet** : Détection automatique d'encodage

## Support

Pour toute question ou problème, consulter les logs dans le répertoire `logs/` et les tables d'audit en base de données.

