# Database as Crime Scene

> A PostgreSQL performance analysis and optimization toolkit framed as a forensic investigation. Slow queries, missing indexes, and suboptimal schemas are the "crimes" — `EXPLAIN ANALYZE`, index statistics, and query plans are your forensic tools.

Built around a Twitter/X-like social schema (users, posts, comments, friends) plus large time-series tables (metrics, events, logs) for demonstrating real-world performance problems and their remedies.

## Table of Contents

- [Quick Start](#quick-start)
- [The Crime Scene Metaphor](#the-crime-scene-metaphor)
- [Database Schema](#database-schema)
- [Forensic Tools](#forensic-tools)
- [Notebooks](#notebooks)
- [Task Reference](#task-reference)
- [Connection Details](#connection-details)
- [Tech Stack](#tech-stack)

---

## Quick Start

```bash
# Start PostgreSQL + Jupyter (resets all data)
task local:up:refresh

# Seed with fake data (10,000 users + posts, comments, friendships)
task local:database:seed:large
```

Open **localhost:8888** and run the notebooks in order.

## The Crime Scene Metaphor

Poor database performance is treated as a **crime scene**:

| Concept | Forensic Analogy |
|---|---|
| Slow queries | The crime |
| `pg_stat_user_indexes` | Witness statements |
| `pg_stats` (selectivity) | Physical evidence |
| `EXPLAIN ANALYZE` | Autopsy report |
| Unused/bloated indexes | Murder weapons |
| Schema denormalization | Scene cleanup |

## Database Schema

| Table | Purpose | Rows (default seed) |
|---|---|---|
| `users_profile` | User accounts | 10,000 |
| `posts` | User posts | ~150,000 |
| `comments` | Comments on posts | ~800,000 |
| `friends` | Bidirectional friendships | ~200,000 |
| `metrics` | Time-series metrics | 10,000,000 |
| `events` | User events | 10,000,000 |
| `logs` | Application logs | 10,000,000 |

Relationships: `users_profile 1--* posts 1--* comments`, `users_profile 1--* friends`.

## Forensic Tools

**`forensic/forensic.py`** — The `Forensic` dataclass examines index health:
- `check_indexes()` — Queries `pg_stat_user_indexes` and `pg_stats`, classifies each index as `PK`, `UNIQUE`, `CRITICAL` (unused but large), `SUSPICIOUS` (rarely used), or `HEALTHY`, and computes a 0–100 health score.

**`jupyter/mermaid_execution_plan.py`** — Converts an `EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON)` plan into a color-coded Mermaid flowchart. Nodes are marked **fast** (green), **medium** (yellow), or **slow** (red).

**`jupyter/mermaid.py`** — Generates Mermaid ER diagrams from table/view metadata, rendered via `mermaid.ink`.

**`db/connection.py`** — `get_execution_plan()` runs annotated `EXPLAIN` and returns structured JSON.

**`common/logger.py`** — Rich-formatted logging with SQL syntax highlighting, table rendering, JSON tree views, and markdown output.

## Notebooks

| # | Notebook | What you'll learn |
|---|---|---|
| 00 | `00_setup.ipynb` | Load extensions, verify connectivity |
| 01 | `01_discovery.ipynb` | Explore schema, ER diagrams, row counts |
| 02 | `02_indexes.ipynb` | **Core forensic analysis** — run `Forensic.check_indexes()`, classify indexes, compute scores |
| 03 | `03_materialized_views.ipynb` | Speed up expensive aggregations with precomputed views |
| 04 | `04_denormalization.ipynb` | Trade off write complexity for read performance |
| 05 | `05_replication.ipynb` | Read scaling strategies |
| 06 | `06_partitioning.ipynb` | Table partitioning by time on metrics/events/logs |
| 07 | `07_query_optimization.ipynb` | `EXPLAIN ANALYZE` deep-dive with execution plan visualization |
| — | `use_case.ipynb` | **End-to-end** — combine all techniques on a realistic workload |

## Task Reference

```bash
# Docker lifecycle
task local:up               # Start containers (rebuild images)
task local:up:refresh       # Reset volumes + start fresh
task local:init             # up:refresh + wait + seed (default)
task local:jupyter:bash     # Shell into Jupyter container

# Seeding
task local:database:seed         # Custom: task local:database:seed -- 100 5 3 10
task local:database:seed:small   # 10 users
task local:database:seed:medium  # 1,000 users
task local:database:seed:large   # 10,000 users

# Forensic analysis (CLI)
task local:forensic:check-indexes   # Run Forensic.check_indexes() from command line

# SQL explain plans
task local:database:explaing:user_feed
task local:database:explaing:post_with_comments
task local:database:explaing:friends_posts

# Schema visualization (SchemaCrawler)
task schemacrawler:graphviz          # ER diagram (PNG) with row counts
task schemacrawler:graphviz:indexes  # ER diagram with index annotations
task schemacrawler:mermaid           # ER diagram as Mermaid
task schemacrawler:dbml              # Schema in DBML format
task schemacrawler:json              # Full schema metadata as JSON
task schemacrawler:all               # All SchemaCrawler outputs

# Code quality
task python:review   # Run black, isort, ruff, pylint

# Code diagrams
task code:generate-diagram              # UML class/package diagrams (pyreverse)
task code:generate-diagram:mermaid       # Code structure as Mermaid
task code:generate-diagram:pydeps        # Dependency graph
task code:generate-diagram:py2puml       # PlantUML class diagram
```

## Connection Details

| Parameter | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Database | `mydb` |
| Username | `postgres` |
| Password | `postgres` |

```bash
# psql inside the container
docker exec -it postgres_db psql -U postgres -d mydb

# From host (if psql is installed)
psql -h localhost -U postgres -d mydb
```

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 16 (Alpine) |
| Backend | Python 3.11+ / SQLAlchemy / pandas |
| Notebooks | Jupyter Lab with `jupysql` |
| Logging | `rich` + `rich-tools` |
| Testing | pytest / pytest-mock |
| Linting | ruff / black / isort / pylint |
| Task runner | Taskfile |
| Schema viz | SchemaCrawler 17.x (Docker) |
| Data | Faker |
