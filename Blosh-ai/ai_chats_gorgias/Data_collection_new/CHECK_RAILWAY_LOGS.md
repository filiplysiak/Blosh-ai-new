# How to Check Railway Logs for the New Deployment

## ⚠️ Important: You're Looking at OLD Logs!

The logs showing errors are from the **old deployment (d380cc76)** that was removed on Oct 30, 2025.

Your **new deployment was successful 58 seconds ago** - you need to check the CURRENT deployment logs.

## How to View Current Deployment Logs

### Step 1: Find the Active Deployment
In Railway dashboard:
1. Click on your **Blosh-ai-new** service
2. Look at the **Deployments** tab
3. Find the **ACTIVE** deployment (should be at the top)
4. It should show: **"Deployment successful - 58 seconds ago"** (or similar recent time)

### Step 2: View the Correct Logs
1. Click on the **active/current deployment** (NOT the removed one)
2. Click on **"Deploy Logs"** tab to see startup logs
3. Click on **"HTTP Logs"** tab to see API request logs
4. Make sure you're NOT looking at deployment "d380cc76" (that's the old one)

### Step 3: What to Look For

#### In Deploy Logs (Startup):
```
✅ 🚀 Gorgias AI Widget Server
✅ OpenAI API Key: ✓ Set
✅ Gorgias Auth: ✓ Set
✅ Gorgias URL: https://freebirdicons.gorgias.com/api
✅ Running on http://0.0.0.0:XXXX
```

#### In HTTP Logs (When Gorgias Sends Request):
**OLD (Error):**
```
❌ ERROR:API_widget_server:Error in suggest_response: 'list' object has no attribute 'get'
```

**NEW (Fixed):**
```
✅ INFO:API_widget_server:Received raw data type: <class 'list'>
✅ INFO:API_widget_server:Received raw data: [{'ticket_id': '123456', ...}]
✅ INFO:API_widget_server:Extracted data from list format
✅ INFO:API_widget_server:Generating suggestion for ticket 123456
✅ INFO:API_widget_server:Generated suggestion for 123456 - Quality: 85
```

## How to Trigger a New Request

To see the fix in action:

### Option 1: Test from Gorgias
1. Open any ticket in Gorgias
2. The AI widget should load (may take 10-30 seconds first time)
3. Check Railway logs for the new request

### Option 2: Test with curl
```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/suggest \
  -H "Content-Type: application/json" \
  -d '[{"ticket_id": "123456"}]'
```

### Option 3: Test Health Endpoint
```bash
curl https://blosh-ai-new-production.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T..."
}
```

## Clearing Old Logs

The old error logs will remain in Railway's history, but they're from the old deployment. Focus on:
- ✅ New deployment shows "successful"
- ✅ New requests don't show errors
- ✅ HTTP logs show "Extracted data from list format"

## If You Still See Errors in NEW Deployment

1. **Check the deployment ID** - Make sure you're not looking at "d380cc76"
2. **Check Build Logs** - Verify the new code was deployed
3. **Trigger a new request** - Old logs won't disappear, you need new traffic
4. **Check environment variables** - Make sure OPENAI_API_KEY is set

## Quick Verification Checklist

- [ ] Active deployment shows "Deployment successful"
- [ ] Active deployment is NOT "d380cc76" (that's old)
- [ ] Deploy Logs show server started successfully
- [ ] Triggered a new request (via Gorgias or curl)
- [ ] HTTP Logs show "Extracted data from list format" (not the old error)
- [ ] No new AttributeError messages appearing

## Railway Dashboard Navigation

```
Railway Dashboard
  └── Blosh-ai-new (your project)
      └── Blosh-ai-new (your service)
          └── Deployments tab
              ├── [ACTIVE] Latest deployment ← CHECK THIS ONE
              │   ├── Build Logs
              │   ├── Deploy Logs
              │   └── HTTP Logs
              │
              └── [REMOVED] d380cc76 ← IGNORE THIS ONE (old errors)
```

---

**Remember:** The old error logs are historical. They won't disappear. You need to:
1. Verify the NEW deployment is active
2. Trigger a NEW request
3. Check logs for the NEW request (should show "Extracted data from list format")

The fix is deployed! You just need to look at the right logs. 🎉

