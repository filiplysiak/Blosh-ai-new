# Gorgias AI Widget - Setup Guide

AI-powered response suggestions for Gorgias using fine-tuned GPT-4o-mini.

## Core Files

- `API_widget_server.py` - Flask API server & widget HTML
- `database.py` - SQLite persistence layer for tickets & suggestions
- `ticket_sync.py` - Sync utilities pulling tickets from Gorgias
- `suggestion_manager.py` - Background generation & pre-generation orchestration
- `gorgias_client.py` - Thin Gorgias REST API client
- `improved_response_generator.py` - AI response logic (fine-tuned model)
- `requirements.txt` - Python dependencies (includes APScheduler for cron jobs)
- `Procfile` - Railway deployment config

## Quick Setup

### Step 1: Get Your API Keys (5 minutes)

#### A. OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy it (starts with `sk-proj-...`)

#### B. Gorgias API Authentication
1. Go to Gorgias → Settings → REST API
2. Create API key (or use existing)
3. Note your email and API key
4. Encode it as Base64:

**Windows PowerShell:**
```powershell
$text = "your-email@example.com:your-api-key"
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text))
```

**Linux/Mac:**
```bash
echo -n "your-email@example.com:your-api-key" | base64
```

5. Add "Basic " prefix to the result:
```
Basic YourBase64StringHere
```

---

### Step 2: Deploy to Railway (15 minutes)

#### A. Push to GitHub (if needed)
```bash
cd c:\GitHub\Blosh-ai-new
git add .
git commit -m "Gorgias widget ready for deployment"
git push origin main
```

#### B. Deploy on Railway

1. **Go to**: https://railway.app/
2. **Sign up** with your GitHub account
3. **New Project** → "Deploy from GitHub repo"
4. **Select**: `Blosh-ai-new` repository
5. **Railway will auto-detect** Python and use the Procfile

#### C. Add Environment Variables

In Railway project → **Variables** tab, add:

```
OPENAI_API_KEY
sk-proj-your-actual-openai-key-here

GORGIAS_AUTH
Basic your-base64-encoded-auth-here

GORGIAS_BASE_URL
https://freebirdicons.gorgias.com/api

# optional – override SQLite location (defaults to data/widget.db)
WIDGET_DB_PATH
/data/widget.db
```

**Important**: Replace `freebirdicons` with YOUR Gorgias subdomain!

#### D. Wait for Deployment
- Railway will automatically deploy (2-3 minutes)
- You'll get a URL like: `https://blosh-ai-production.up.railway.app`
- **Copy this URL** - you'll need it!

#### E. Test Deployment
```bash
# Replace YOUR_URL with your actual Railway URL
curl https://YOUR_URL/health
```

Should return:
```json
{"status":"healthy","timestamp":"2025-10-30T..."}
```

---

### Step 3: Configure Gorgias Widget (10 minutes)

1. **Go to Gorgias**: Settings → Productivity → Widgets

2. **Add Widget**: Click "+ Add Widget"

3. **Configure**:
   - **Name**: `AI Response Suggestion`
   - **Type**: Select **"Custom HTML"**
   - **HTML Code**: Paste this (replace `YOUR_URL`):
   
```html
<iframe 
  src="https://YOUR_URL/widget/{{ticket.id}}" 
  width="100%" 
  height="700px" 
  frameborder="0"
  style="border: none; min-height: 700px;"
></iframe>
```

4. **Display Conditions**:
   - When to show: **"Ticket is open"**
   - (Optional) Add: "Ticket has customer message"

5. **Position**:
   - Location: **Right Sidebar**
   - Drag it to a high position in the layout

6. **Save** and **Enable** the widget

---

### Step 4: Test

1. Open ticket in Gorgias
2. Check right sidebar for AI suggestions
3. Test Copy/Use buttons
   - Click "Use Response" → copies and records feedback
   - Click feedback buttons → tracks your feedback

---

## Troubleshooting

**Widget loading forever**: Check Railway logs, verify environment variables  
**No message found**: Verify `GORGIAS_AUTH` format: `Basic [base64]`  
**Widget not appearing**: Enable widget in Gorgias Settings → Widgets  

## Local Testing

```bash
export OPENAI_API_KEY=sk-proj-...
export GORGIAS_AUTH=Basic ...
python API_widget_server.py
```

## Features

- Persistent SQLite storage of all tickets & AI suggestions
- Automatic sync of latest tickets from Gorgias (boot + every 5 minutes)
- Pre-generation for the 10 most recent tickets via background worker pool
- On-demand generation per ticket with inline sidebar UI (no popups)
- Fine-tuned model: `ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB`
- Brand detection (Freebird/Simple) with quality scoring & safety checks
- Feedback tracking endpoint for future analytics

## Cost Estimate

- Railway: $5-20/month
- OpenAI API: $9-45/month (usage-based)
- Total: $14-65/month  

