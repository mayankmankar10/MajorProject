# Docker Setup Guide - Preserving Existing Data

This guide explains how to containerize your application while **preserving** your existing database and vector embeddings.

## What Gets Preserved

✅ **SQLite Database** (`manpower.db`)
- All employees, jobs, applications, offers
- User accounts and authentication data
- All historical data

✅ **FAISS Vector Indexes**
- Employee embeddings (`employee_index`)
- Job embeddings (`job_index`)
- All semantic search data

---

## Quick Start

### 1. Build and Run Containers

```powershell
# Build images
docker-compose build

# Start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Access Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Volume Mounts (Data Persistence)

The `docker-compose.yml` mounts your existing data:

```yaml
volumes:
  - ./manpower.db:/app/manpower.db                    # SQLite database
  - ./backend/db/faiss_indexes:/app/backend/db/faiss_indexes  # Vector indexes
  - ./vectors:/app/vectors                             # Additional vectors
```

**This means:**
- Changes in the container update your local files
- Your data persists even if containers are deleted
- No data migration needed!

---

## Useful Commands

```powershell
# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Execute commands in backend container
docker-compose exec backend python generate_embeddings.py

# Access backend shell
docker-compose exec backend bash

# Remove containers (data persists)
docker-compose down

# Remove containers AND volumes (⚠️ deletes data)
docker-compose down -v
```

---

## Environment Variables

Make sure your `.env` file contains:

```env
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./manpower.db
```

---

## Backup Your Data

Before containerizing, backup your data:

```powershell
# Backup database
copy manpower.db manpower.db.backup

# Backup vector indexes
xcopy /E /I backend\db\faiss_indexes backend\db\faiss_indexes.backup
```

---

## Troubleshooting

### Database locked error
- Stop the local backend: `Ctrl+C` on uvicorn terminal
- Ensure no other processes are using `manpower.db`

### Vectors not found
- Check that `backend/db/faiss_indexes/` contains:
  - `employee_index/` folder
  - `job_index/` folder
- Run embeddings generation if needed:
  ```powershell
  docker-compose exec backend python backend/scripts/migrate_embeddings.py
  docker-compose exec backend python regenerate_job_embeddings.py
  ```

### Port already in use
- Change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Backend
    - "5174:5173"  # Frontend
  ```

---

## Production Deployment

For production, consider:

1. **Use PostgreSQL** instead of SQLite
2. **Use managed vector DB** (Pinecone, Weaviate, etc.)
3. **Add nginx** reverse proxy
4. **Enable HTTPS** with SSL certificates
5. **Set up CI/CD** pipeline

---

## Next Steps

1. Test the containerized app locally
2. Verify all features work (bulk hire, auto-fill, job search)
3. Deploy to cloud (AWS, GCP, Azure, DigitalOcean)
4. Set up monitoring and logging
