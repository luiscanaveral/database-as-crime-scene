# 
sometimes, Urgent incidents drives you to 

# PostgreSQL Docker Setup

A simple Docker Compose setup for PostgreSQL with initialization script.
## Prerequisites

- docker
- plantuml

## Quick Start

```bash
task local:up:refresh  
# Seed with mock data
task local:database:seed:large    


```
Brownse on localhost:8888

```bash
## Optional operations
task schemacrawler:graphviz:indexes
```

## Connection Details

- Host: localhost
- Port: 5432
- Database: mydb
- Username: postgres
- Password: postgres

## Connect to Database

```bash
# Using psql
docker exec -it postgres_db psql -U postgres -d mydb

# Or connect from host (if psql is installed)
psql -h localhost -U postgres -d mydb
```
