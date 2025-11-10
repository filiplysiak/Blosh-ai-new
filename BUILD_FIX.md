# Railway Build Fix - "pip: not found"

## The Problem

Railway build was failing with:
```
pip install -r API_widget_requirements.txt
sh: 1: pip: not found
ERROR: failed to build: exit code: 127
```

## Root Cause

Railway's Nixpacks was trying to install from `API_widget_requirements.txt` in a subdirectory, but:
1. Python environment wasn't set up yet
2. `pip` wasn't available in the build context
3. Wrong requirements file was being detected

## The Fix

Created two configuration files to tell Railway how to build properly:

### 1. `railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd Blosh-ai/ai_chats_gorgias/Data_collection_new && gunicorn API_widget_server:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 2. `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "pip"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = []

[start]
cmd = "cd Blosh-ai/ai_chats_gorgias/Data_collection_new && gunicorn API_widget_server:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120"
```

## What This Does

1. **Setup Phase:** Installs Python 3.11 and pip
2. **Install Phase:** Runs `pip install -r requirements.txt` (root file)
3. **Start Phase:** Changes to correct directory and starts gunicorn

## Deployment

**Commit:** `e9b6026`  
**Status:** Pushed to Railway  
**ETA:** 2-3 minutes (full rebuild)

## Expected Build Logs

After this fix, you should see:

```
✅ [setup] Installing python311, pip
✅ [install] pip install -r requirements.txt
✅ Collecting Flask>=3.0.0
✅ Collecting flask-cors>=4.0.0
✅ Collecting gunicorn>=21.2.0
✅ Collecting openai>=1.6.1
✅ Successfully installed Flask-3.0.0 ...
✅ [start] Starting gunicorn
✅ Listening at: http://0.0.0.0:8080
```

## Why It Was Failing

Railway's auto-detection found `API_widget_requirements.txt` and tried to use it, but:
- File is in subdirectory
- Python wasn't installed yet
- pip wasn't available
- Build failed before even starting

## Files Structure

```
Blosh-ai-new/
├── requirements.txt              ← Railway uses THIS (root)
├── Procfile                      ← Deployment command
├── railway.toml                  ← NEW: Railway config
├── nixpacks.toml                 ← NEW: Build config
├── runtime.txt                   ← Python version
└── Blosh-ai/
    └── ai_chats_gorgias/
        └── Data_collection_new/
            ├── API_widget_server.py
            ├── improved_response_generator.py
            └── API_widget_requirements.txt  ← Not used by Railway
```

## What to Check

### 1. Wait for Build to Complete (2-3 minutes)

Railway needs to:
- Download Python 3.11
- Install pip
- Install all dependencies
- Start gunicorn

### 2. Check Build Logs

Look for:
```
✅ [setup] Installing python311, pip
✅ [install] pip install -r requirements.txt
✅ Successfully installed ...
```

### 3. Check Deploy Logs

Look for:
```
✅ Starting gunicorn 23.0.0
✅ Listening at: http://0.0.0.0:8080
✅ Booting worker with pid: 2
✅ Booting worker with pid: 3
```

**And it should NOT crash after this!**

### 4. Test Health Endpoint

Once deployed:
```bash
curl https://blosh-ai-new-production.up.railway.app/health
```

Should return:
```json
{"status": "healthy", "timestamp": "..."}
```

## If Still Failing

Check Railway logs for:
- "OPENAI_API_KEY environment variable is required"
- If you see this, add the variable in Railway → Variables

## Timeline

- **10:37 AM** - Previous build failed (pip not found)
- **10:40 AM** - Added railway.toml and nixpacks.toml
- **10:42 AM** - Deploying fix...
- **10:45 AM** - Should be fully deployed

## After Successful Deployment

1. ✅ Server starts without crashing
2. ✅ Health endpoint responds
3. ✅ Widget loads in Gorgias
4. ✅ AI suggestions generate properly
5. ✅ Everything works!

---

**Status:** Fix deployed, waiting for Railway to rebuild... 🔨

