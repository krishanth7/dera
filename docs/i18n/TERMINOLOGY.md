# DERA Technical Terminology Glossary

This glossary establishes the canonical translation of core database engineering, reverse-analysis, and graph theory concepts across DERA's **ten official documentation languages**.

All translations must adhere to these terms to ensure semantic consistency, technical precision, and cross-lingual parity.

---

## 1. Core Terminology Matrix

| Concept (English) | Español (es) | Français (fr) | Deutsch (de) | Português (pt) | Italiano (it) | 日本語 (ja) | 한국어 (ko) | 简体中文 (zh-CN) | Русский (ru) |
|---|---|---|---|---|---|---|---|---|---|
| **Database Schema** | Esquema de base de datos | Schéma de base de données | Datenbankschema | Esquema de banco de dados | Schema di database | データベーススキーマ | 데이터베이스 스키마 | 数据库模式 / 架构 | Схема базы данных |
| **Metadata** | Metadatos | Métadonnées | Metadaten | Metadados | Metadati | メタデータ | 메타데이터 | 元数据 | Метаданные |
| **Schema Introspection** | Introspección de esquemas | Introspection de schéma | Schemaintrospektion | Introspecção de esquema | Introspezione dello schema | スキーマイントロスペクション | 스키마 인트로스펙션 (검사) | 模式内省 / 自省 | Интроспекция схемы |
| **Reverse Engineering** | Ingeniería inversa | Rétro-ingénierie | Reverse Engineering | Engenharia reversa | Ingegneria inversa | リバースエンジニアリング | 리버스 엔지니어링 (역공학) | 逆向工程 | Обратная инженерия |
| **Primary Key** | Clave primaria | Clé primaire | Primärschlüssel | Chave primária | Chiave primaria | 主キー | 기본 키 (PK) | 主键 | Первичный ключ |
| **Foreign Key** | Clave foránea | Clé étrangère | Fremdschlüssel | Chave estrangeira | Chiave esterna | 外部キー | 외래 키 (FK) | 外键 | Внешний ключ |
| **Composite Key** | Clave compuesta | Clé composite | Zusammengesetzter Schlüssel | Chave composta | Chiave composita | 複合キー | 복합 키 | 复合键 | Составной ключ |
| **Constraint** | Restricción | Contrainte | Integritätsbedingung / Constraint | Restrição | Vincolo | 制約 | 제약 조건 | 约束 | Ограничение |
| **Index** | Índice | Index | Index | Índice | Indice | インデックス | 인덱스 | 索引 | Индекс |
| **Dependency Graph** | Grafo de dependencias | Graphe de dépendances | Abhängigkeitsgraph | Grafo de dependências | Grafo delle dipendenze | 依存関係グラフ | 의존성 그래프 | 依赖关系图 | Граф зависимостей |
| **Schema Snapshot** | Instantánea del esquema | Instantané de schéma | Schema-Snapshot | Instantâneo de esquema | Snapshot dello schema | スキーマスナップショット | 스키마 스냅샷 | 模式快照 | Снимок схемы |
| **Schema Diff** | Diferencia de esquemas | Diff de schéma | Schema-Diff / Schemavergleich | Diferença de esquemas | Diff dello schema | スキーマ差分 | 스키마 비교 (Diff) | 模式差异对比 | Различия схем (Diff) |
| **Migration Preview** | Vista previa de migración | Prévisualisation de migration | Migrationsvorschau | Pré-visualização de migração | Anteprima della migrazione | マイグレーションプレビュー | 마이그레이션 미리보기 | 迁移预览 | Предпросмотр миграции |
| **Read-Only Connection** | Conexión de solo lectura | Connexion en lecture seule | Schreibgeschützte Verbindung | Conexão somente leitura | Connessione di sola lettura | 読み取り専用接続 | 읽기 전용 연결 | 只读连接 | Подключение только для чтения |
| **Deterministic Analysis** | Análisis determinista | Analyse déterministe | Deterministische Analyse | Análise determinística | Analisi deterministica | 決定論的解析 | 결정론적 분석 | 确定性分析 | Детерминированный анализ |
| **Database Connector** | Conector de base de datos | Connecteur de base de données | Datenbank-Konnektor | Conector de banco de dados | Connettore di database | データベースコネクタ | 데이터베이스 커넥터 | 数据库连接器 | Коннектор базы данных |

---

## 2. Branding & Identity Rules

1. **Project Name:** Always written in capital letters as **`DERA`**.
2. **Project Expansion:** **`Database Engineering & Reverse Analysis`** is maintained across all technical documentation headers.
3. **Official Tagline:**
   - English (Canonical): *"Understand Every Schema. Engineer Every Change."*
   - Español: *"Comprende cada esquema. Diseña cada cambio."*
   - Français: *"Comprenez chaque schéma. Concevez chaque changement."*
   - Deutsch: *"Verstehe jedes Schema. Entwickle jede Änderung."*
   - Português: *"Compreenda cada esquema. Projete cada mudança."*
   - Italiano: *"Comprendi ogni schema. Progetta ogni cambiamento."*
   - 日本語: *"すべてのスキーマを理解し、すべての変更を設計する。"*
   - 한국어: *"모든 스키마를 이해하고, 모든 변경을 엔지니어링하십시오."*
   - 简体中文: *"洞悉每个模式，掌控每次变更。"*
   - Русский: *"Понимайте каждую схему. Проектируйте каждое изменение."*

---

## 3. Preserved Code & CLI Identifiers

The following items must **never** be translated:
- CLI tool names and commands (`python scripts/development/dev.py all`, `uvicorn`, `npm run dev:web`, `pytest`, `git clone`).
- Package names and paths (`apps/api`, `apps/web`, `packages/core`, `packages/connectors`, `packages/contracts`).
- SQL keywords, catalog views, and system tables (`information_schema`, `pg_catalog`, `sqlite_master`, `PRAGMA foreign_key_list`).
- Technical identifiers in code (`SchemaSnapshot`, `Table`, `Column`, `ForeignKeyConstraint`, `DependencyGraph`, `get_table_dependencies`).
- Environment variables (`DERA_ENV`, `DERA_HOST`, `DERA_PORT`, `DERA_DATABASE_URL`).
- License identifiers (`MIT License`, `Copyright (c) 2026 Krishanth`).
