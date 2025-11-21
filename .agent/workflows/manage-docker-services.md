---
description: manage Docker services
---

# Manage Docker Services

This workflow helps you manage the Docker services (Qdrant, PostgreSQL, pgAdmin).

## Start All Services

// turbo
1. Start all services in detached mode:
   ```bash
   docker-compose up -d
   ```

## Start Specific Services

// turbo
2. Start only specific services:
   ```bash
   docker-compose up -d qdrant postgres
   ```

## Stop All Services

// turbo
3. Stop all running services:
   ```bash
   docker-compose down
   ```

## Stop and Remove Volumes (CAUTION: Data Loss)

4. Stop services and remove all data volumes:
   ```bash
   docker-compose down -v
   ```
   ⚠️ This will delete all database and vector data!

## View Service Status

// turbo
5. Check status of all services:
   ```bash
   docker-compose ps
   ```

## View Service Logs

// turbo
6. View logs from all services:
   ```bash
   docker-compose logs
   ```

// turbo
7. View logs from a specific service:
   ```bash
   docker-compose logs postgres
   ```

// turbo
8. Follow logs in real-time:
   ```bash
   docker-compose logs -f
   ```

## Restart Services

// turbo
9. Restart all services:
   ```bash
   docker-compose restart
   ```

// turbo
10. Restart a specific service:
    ```bash
    docker-compose restart postgres
    ```

## Access Services

11. Access PostgreSQL with psql:
    ```bash
    docker exec -it postgres-rag psql -U <username> -d agentic_rag
    ```

12. Access pgAdmin:
    - Open browser to http://localhost:5050
    - Login with credentials from .env file

13. Access Qdrant dashboard:
    - Open browser to http://localhost:6333/dashboard

## Rebuild Services

14. Rebuild and start services (after config changes):
    ```bash
    docker-compose up -d --build
    ```

## Clean Up

// turbo
15. Remove stopped containers:
    ```bash
    docker-compose rm
    ```

16. Clean up all unused Docker resources:
    ```bash
    docker system prune -a
    ```

## Service Ports

- PostgreSQL: 5432
- pgAdmin: 5050
- Qdrant HTTP: 6333
- Qdrant gRPC: 6334

## Tips

- Always use `-d` flag to run in detached mode for development
- Check logs if services fail to start
- Use `docker-compose ps` to verify all services are healthy
- Backup data volumes before running `down -v`
