# How to Clone the Repository

## Prerequisites
- Git installed ([download here](https://git-scm.com/downloads))
- GitHub account (if repo is private)

---

## Step 1: Get the Repository URL

### If on GitHub:
1. Go to your repository on GitHub
2. Click the green **"Code"** button
3. Copy the URL (HTTPS or SSH)

**Example URLs:**
- HTTPS: `https://github.com/yourusername/manpower_connector.git`
- SSH: `git@github.com:yourusername/manpower_connector.git`

---

## Step 2: Clone the Repository

### Using Command Line:

**Windows (PowerShell):**
```powershell
# Navigate to where you want the project
cd C:\Projects

# Clone the repository
git clone https://github.com/yourusername/manpower_connector.git

# Enter the project folder
cd manpower_connector
```

**Mac/Linux:**
```bash
# Navigate to where you want the project
cd ~/Projects

# Clone the repository
git clone https://github.com/yourusername/manpower_connector.git

# Enter the project folder
cd manpower_connector
```

### Using VS Code:
1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
3. Type "Git: Clone"
4. Paste the repository URL
5. Choose a folder location
6. Open the cloned repository

### Using GitHub Desktop:
1. Open GitHub Desktop
2. File → Clone Repository
3. Enter the URL or select from your GitHub repos
4. Choose local path
5. Click "Clone"

---

## Step 3: Verify the Clone

```powershell
# Check if files are there
ls

# You should see:
# - backend/
# - frontend/
# - docker-compose.yml
# - README.md
# - .env.example
# etc.
```

---

## Step 4: Set Up Environment

```powershell
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# (Use notepad, VS Code, or any text editor)
```

---

## Troubleshooting

### "git: command not found"
**Solution:** Install Git from https://git-scm.com/downloads

### "Permission denied (publickey)"
**Solution:** Use HTTPS URL instead of SSH, or set up SSH keys

### "Repository not found"
**Solution:** 
- Check the URL is correct
- Ensure you have access to the repository
- If private, make sure you're logged into GitHub

---

## Next Steps

After cloning:
1. ✅ Create `.env` file from `.env.example`
2. ✅ Add your API keys
3. ✅ Run `docker-compose up -d --build`
4. ✅ Access at http://localhost:5173

---

## Quick Reference

```bash
# Clone
git clone <repository-url>

# Update (pull latest changes)
git pull

# Check status
git status

# View branches
git branch -a
```
