# Manpower Connector

A comprehensive AI-powered hiring platform for the hospitality industry.

---

## ✅ Setup Complete!

Your colleague can now:

1. **Clone the repository**
2. **Copy `.env.example` to `.env`** and add their API keys
3. **Run `docker-compose up -d --build`**
4. **Access at http://localhost:5173**

---

## What They Get

- ✅ **Isolated environment** - No conflicts with your setup
- ✅ **Own database** - Fresh start or copy yours
- ✅ **Own API keys** - No rate limit conflicts
- ✅ **Same features** - Full application functionality

---

## Files to Share

Share these files/folders with your colleague:

**Required:**
- `docker-compose.yml`
- `Dockerfile`
- `frontend/Dockerfile`
- `.dockerignore`
- `.env.example` (they create their own `.env`)
- `README.md`
- `backend/` (all backend code)
- `frontend/` (all frontend code)
- `requirements.txt`

**Optional (for existing data):**
- `manpower.db` (if they want your data)
- `backend/db/faiss_indexes/` (if they want your embeddings)

**Don't share:**
- `.env` (contains your API keys!)
- `node_modules/`
- `__pycache__/`
- `.venv/`

---

## How to Share

### Option 1: Git Repository (Recommended)

```powershell
# Initialize Git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit"

# Push to GitHub
git remote add origin https://github.com/yourusername/manpower-connector.git
git push -u origin main
```

**Your colleague:**
```powershell
git clone https://github.com/yourusername/manpower-connector.git
cd manpower-connector
cp .env.example .env
# Edit .env with their API keys
docker-compose up -d --build
```

### Option 2: Zip File

```powershell
# Create zip (exclude unnecessary files)
Compress-Archive -Path * -DestinationPath manpower-connector.zip -Exclude node_modules,__pycache__,.venv,.env,*.db
```

Send `manpower-connector.zip` to your colleague.

---

## Next Steps

1. ✅ Share repository or zip file
2. ✅ Send colleague the setup guide
3. ✅ They set up their own instance
4. ✅ Both work independently - no conflicts!

---

## Support

If your colleague has issues:
1. Check `COLLEAGUE_SETUP_GUIDE.md`
2. Run `docker-compose logs -f`
3. Rebuild: `docker-compose up -d --build`
