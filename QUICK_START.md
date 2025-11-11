# 🚀 Quick Start Guide - Gorgias AI Widget

## ⚡ Deploy in 5 Minutes

### Step 1: Set Environment Variables in Railway (2 min)

Go to your Railway project → **Variables** tab:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
GORGIAS_AUTH=Basic your-base64-encoded-auth-here
GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
```

**How to get GORGIAS_AUTH:**
```powershell
# Windows PowerShell
$text = "your-email@example.com:your-api-key"
$base64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text))
Write-Output "Basic $base64"
```

### Step 2: Deploy to Railway (1 min)

```bash
git add .
git commit -m "Production-ready widget with rate limiting and pre-generation"
git push origin main
```

Railway will automatically deploy. Wait for "Deployed" status.

### Step 3: Verify Deployment (1 min)

```bash
# Replace YOUR_URL with your Railway URL
curl https://YOUR_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-11T...",
  "initialized": true,
  "database": {
    "tickets": 10,
    "suggestions": 8,
    "queue": {"pending": 2}
  }
}
```

### Step 4: Check Stats (1 min)

```bash
curl https://YOUR_URL/api/stats
```

You should see:
- Recent tickets synced
- Top tickets with suggestions
- Queue status
- Rate limiter info

---

## ✅ What's Working Now

### 🎯 Rate Limiting
- **10 requests/minute** to OpenAI API
- **Burst capacity**: 3 requests
- **Automatic throttling**: No API errors

### 🚀 Pre-generation
- **Top 10 recent tickets** always have suggestions ready
- **Instant loading**: < 100ms for pre-generated
- **Smart caching**: No duplicate generations

### 🔄 Auto-sync
- **Every 10 minutes**: Fetches recent tickets
- **On startup**: Syncs 100 tickets initially
- **Background**: Non-blocking operation

### 📊 Monitoring
- `/health` - Health check
- `/api/stats` - Detailed statistics
- Railway logs - Full activity log

---

## 🧪 Test the Widget

### 1. Open Gorgias
Go to any ticket in your Gorgias dashboard

### 2. Check Right Sidebar
You should see "🤖 AI Suggestion" widget

### 3. Test Features
- ✅ Suggestion displays instantly (if pre-generated)
- ✅ "Use Response" button copies to clipboard
- ✅ "Copy" button copies text
- ✅ "Regenerate" button creates new suggestion
- ✅ Feedback buttons track usage

---

## 📊 Monitor Performance

### Railway Dashboard
- **Logs**: Real-time activity
- **Metrics**: CPU, Memory, Network
- **Deployments**: History and rollback

### Key Log Messages to Look For

✅ **Good Signs:**
```
✅ Synced X tickets during initialization
✅ Generated suggestion for ticket X (quality: Y%)
✅ Background worker started
✅ Scheduled periodic sync every 10 minutes
```

⚠️ **Warnings (Normal):**
```
⚠️ Rate limited, waiting Xs before processing
⚠️ GORGIAS_AUTH not set - skipping ticket sync (if not configured)
```

❌ **Errors (Need Attention):**
```
❌ Failed to generate response for ticket X
❌ Database error: ...
❌ OPENAI_API_KEY not set
```

---

## 🔧 Common Issues & Fixes

### Issue: Widget shows "Loading..." forever

**Check:**
```bash
curl https://YOUR_URL/api/suggest/TICKET_ID
```

**If 404**: Ticket not synced yet
```bash
# Trigger manual sync
curl -X POST https://YOUR_URL/api/sync
```

**If error**: Check Railway logs for details

### Issue: "Rate limiter timeout"

**This is normal!** The system is working correctly:
- Requests are queued
- Processing happens at 10 req/min
- Check queue status: `curl https://YOUR_URL/api/stats`

### Issue: No suggestions generating

**Check OpenAI API key:**
```bash
# In Railway logs, look for:
"OpenAI API Key: ✓ Set"  # Good
"OpenAI API Key: ✗ Not Set"  # Bad - set the env var
```

### Issue: Tickets not syncing

**Check Gorgias auth:**
```bash
# Test manually
curl -H "Authorization: $GORGIAS_AUTH" \
  https://freebirdicons.gorgias.com/api/tickets?limit=1
```

If error: Regenerate GORGIAS_AUTH and update in Railway

---

## 📈 Usage Statistics

### Check Current Stats
```bash
curl https://YOUR_URL/api/stats
```

Response shows:
```json
{
  "database": {
    "tickets": 150,
    "suggestions": 120,
    "queue": {
      "pending": 5,
      "processing": 1,
      "completed": 114
    }
  },
  "top_tickets": [
    {"ticket_id": "12345", "has_suggestion": true},
    ...
  ]
}
```

### Trigger Manual Operations

**Manual sync:**
```bash
curl -X POST https://YOUR_URL/api/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

**Manual initialization:**
```bash
curl -X POST https://YOUR_URL/api/init
```

---

## 🎯 Performance Expectations

### Response Times
- **Pre-generated**: < 100ms ⚡
- **On-demand**: 5-15 seconds ⏱️
- **Sync**: 2-5 seconds per ticket 🔄

### Capacity
- **14,400 suggestions/day** (with rate limiting)
- **100,000+ tickets** in database
- **2 concurrent workers** handling requests

### Costs
- **OpenAI**: ~$0.50 per 1000 suggestions
- **Railway**: $5-20/month
- **Total**: ~$10-30/month for typical usage

---

## 🔐 Security Checklist

- ✅ `OPENAI_API_KEY` set in Railway (not in code)
- ✅ `GORGIAS_AUTH` set in Railway (not in code)
- ✅ CORS configured for Gorgias domains only
- ✅ No sensitive data in logs
- ✅ Database file permissions secure
- ✅ Railway environment variables encrypted

---

## 📞 Support & Debugging

### Check System Health
```bash
# Quick health check
curl https://YOUR_URL/health

# Detailed stats
curl https://YOUR_URL/api/stats

# Test specific ticket
curl https://YOUR_URL/api/suggest/TICKET_ID
```

### Railway Logs
1. Go to Railway dashboard
2. Click on your project
3. Click "View Logs"
4. Filter by error/warning if needed

### Test Locally
```bash
# Set environment variables
export OPENAI_API_KEY=sk-proj-...
export GORGIAS_AUTH=Basic ...

# Run locally
cd Blosh-ai/ai_chats_gorgias/Data_collection_new
python API_widget_server.py

# Test
curl http://localhost:5000/health
```

---

## 🎉 You're All Set!

The system is now:
- ✅ **Deployed** and running on Railway
- ✅ **Rate limited** to prevent API overuse
- ✅ **Pre-generating** suggestions for top 10 tickets
- ✅ **Auto-syncing** every 10 minutes
- ✅ **Monitored** with full stats and logs

**Widget URL**: `https://YOUR_URL/widget/{ticket.id}`

**Next**: Open a ticket in Gorgias and see your AI suggestions! 🚀

