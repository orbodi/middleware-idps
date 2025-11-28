"""
Documentation du micro-middleware IDPS
(contenu simplifié – section models mise à jour pour ne garder que les modèles actuels)
"""

# Micro-Middleware IDPS - Structure Complète

## Architecture Organisée

Le micro-middleware IDPS suit une architecture claire et modulaire :

```
middleware/idps/
├── config/                      # Configuration
│   ├── __init__.py
│   ├── database_config.py       # Configuration base de données
│   └── files_config.py          # Configuration fichiers/répertoires
│
├── models/                      # Classes de mapping
│   ├── __init__.py
│   ├── file_info.py             # IDPSFileInfo
│   ├── workflow_event.py        # IDPSWorkflowEvent
│   ├── error_event.py           # IDPSErrorEvent
│   └── audit_log.py              # IDPSAuditLog
│
├── repository/                  # Accès à la base de données
│   ├── __init__.py
│   └── database_repository.py   # IDPSDatabaseRepository
│
├── services/                     # Services métier
│   ├── __init__.py
│   ├── file_detection_service.py      # Détection de fichiers
│   ├── file_validation_service.py     # Validation CSV
│   ├── data_transformation_service.py # Transformation générique
│   └── file_archive_service.py        # Archivage
│
├── file_pattern.py              # Pattern matching fichiers IDPS
├── validator.py                 # Validation spécifique IDPS
├── transformer.py               # Transformation spécifique IDPS
├── module.py                    # Classe principale (IModule)
│
├── orchestrator.py              # Orchestrateur du processus
├── handler.py                   # Point d'entrée principal
└── scheduler.py                 # Scheduler pour exécution automatique
```

## Composants

### 1. Config (`config/`)
- **`database_config.py`** : Configuration de la base de données PostgreSQL
- **`files_config.py`** : Configuration des répertoires et fichiers CSV

### 2. Models (`models/`)
- **`file_info.py`** : Modèle `IDPSFileInfo` pour les fichiers détectés
- **`workflow_event.py`** : Modèle `IDPSWorkflowEvent` pour les événements workflow
- **`error_event.py`** : Modèle `IDPSErrorEvent` pour les événements d'erreur
- **`audit_log.py`** : Modèle `IDPSAuditLog` pour les logs d'audit

### 3. Repository (`repository/`)
- **`database_repository.py`** : `IDPSDatabaseRepository` pour l'accès à PostgreSQL
  - `insert_events()` : Insertion dans `idps_workflow_events` ou `idps_error_events`
  - `insert_audit_log()` : Insertion dans `idps_ingestion_audit_log`

### 4. Services (`services/`)
- **`file_detection_service.py`** : Détection des fichiers IDPS
- **`file_validation_service.py`** : Validation générique des fichiers CSV
- **`data_transformation_service.py`** : Transformation générique des données
- **`file_archive_service.py`** : Archivage des fichiers traités

### 5. Orchestrateur
- **`orchestrator.py`** : `IDPSOrchestrator` orchestre le processus complet
  - Détection → Validation → Transformation → Chargement → Archivage → Audit

### 6. Handler
- **`handler.py`** : Point d'entrée principal du micro-middleware

### 7. Scheduler
- **`scheduler.py`** : Exécution automatique planifiée (cron-like)

## Utilisation

### Exécution Directe
```bash
python -m middleware.idps.handler
```

### Exécution avec Scheduler
```bash
python -m middleware.idps.scheduler
```

### Via l'Orchestrateur Principal
```bash
python -m middleware.csv_handler
```

## Pipeline d'Ingestion

```
1. FileDetectionService.detect_files()
   ↓
2. FileValidationService.validate_file()
   ↓
3. IDPSValidator.validate_schema()
   ↓
4. DataTransformationService.transform()
   ↓
5. IDPSTransformer.map_to_module_schema()
   ↓
6. IDPSDatabaseRepository.insert_events()
   ↓
7. FileArchiveService.archive_file()
   ↓
8. IDPSDatabaseRepository.insert_audit_log()
```

## Configuration

Les configurations sont chargées depuis les variables d'environnement :
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `INPUT_DIR`, `ARCHIVE_DIR`, `ERROR_DIR`, `LOGS_DIR`
- `CSV_ENCODING`, `CSV_SEPARATOR`, `DATE_FORMAT`

## Base de Données

Tables utilisées :
- `idps_workflow_events` : Événements de workflow (WO-BACKLOG, WO-FINISH)
- `idps_error_events` : Événements d'erreur (QC-ERROR, PERSO-ERROR, SUP-ERROR)
- `idps_ingestion_audit_log` : Logs d'audit des ingestions

