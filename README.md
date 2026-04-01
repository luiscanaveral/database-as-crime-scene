# 
sometimes, Urgent incidents drives you to 

# PostgreSQL Docker Setup

A simple Docker Compose setup for PostgreSQL with initialization script.

## Quick Start

```bash
# Start the database
docker-compose up -d

# Stop the database
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
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
