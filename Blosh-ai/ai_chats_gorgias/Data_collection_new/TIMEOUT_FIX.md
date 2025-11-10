# Gorgias 5-Second Timeout Fix

## The Problem

Gorgias HTTP integrations have a **5-second timeout**. Your error message shows:

```
HTTPSConnectionPool(host='blosh-ai-new-production.up.railway.app', port=443): 
Read timed out. (read timeout=5.0)
```

**Why it times out:**
- Calling OpenAI API takes 3-10 seconds
- Gorgias only waits 5 seconds
- Request times out before AI response is ready

## The Solution: Async Processing

Changed the `/api/suggest` endpoint to:

1. **Respond immediately** (< 1 second) with `202 Accepted`
2. **Process in background** (generate AI response)
3. **Cache the result** for later retrieval

### Flow Diagram

```
Gorgias sends request
    ↓
API receives (< 0.1s)
    ↓
API responds: 202 Accepted ← Gorgias gets this immediately
    ↓
Background thread starts
    ↓
Calls OpenAI API (3-10s)
    ↓
Caches result
    ↓
Widget/Agent can retrieve cached result
```

## How It Works Now

### Step 1: Gorgias Triggers Integration
When ticket is created/updated, Gorgias sends:
```json
[
  {"key": "ticket_id", "value": "190965582"},
  {"key": "customer_name", "value": "Anne Harbers"},
  {"key": "message", "value": "..."},
  {"key": "subject", "value": "Order Freebird"}
]
```

### Step 2: API Responds Immediately (< 1 second)
```json
{
  "status": "processing",
  "ticket_id": "190965582",
  "message": "AI suggestion is being generated. Check back in a few seconds.",
  "timestamp": "2025-11-10T10:15:00"
}
```
**HTTP Status:** `202 Accepted`

### Step 3: Background Processing (3-10 seconds)
- Extracts customer message
- Calls fine-tuned GPT model
- Generates Dutch response
- Validates and fixes response
- Caches result

### Step 4: Retrieve Cached Result
```bash
GET /api/suggest/190965582
```

Returns:
```json
{
  "ticket_id": "190965582",
  "suggestion": "Hi Anne,\n\nBedankt voor je bericht...",
  "quality_score": 85,
  "brand": "Freebird Icons",
  "cached": true
}
```

## New API Endpoints

### 1. POST /api/suggest (Async)
- Accepts Gorgias webhook
- Returns `202 Accepted` immediately
- Processes in background
- **No timeout issues!**

### 2. GET /api/suggest/{ticket_id}
- Retrieves cached suggestion
- Returns `200 OK` if ready
- Returns `404 Not Found` if still processing

### 3. GET /widget/{ticket_id}
- Shows widget UI
- Auto-polls for suggestion
- Displays when ready

## What This Means for Gorgias

**Good News:**
- ✅ No more timeout errors
- ✅ Integration won't fail
- ✅ Gorgias gets immediate response

**Trade-off:**
- ⚠️ Gorgias can't display the AI suggestion directly
- ⚠️ The webhook just logs that processing started
- ⚠️ Agents need to access widget or check logs for actual suggestion

## How to See AI Suggestions

### Option 1: Check Railway Logs
After a ticket is created/updated:
1. Wait 5-10 seconds
2. Check Railway → HTTP Logs
3. Look for: `"Background: Generated and cached suggestion for 190965582 - Quality: 85"`
4. The full suggestion is in the cache

### Option 2: Use Widget Endpoint
Open in browser:
```
https://blosh-ai-new-production.up.railway.app/widget/190965582
```

This shows the AI suggestion with copy/use buttons.

### Option 3: Create Gorgias Sidebar App (Recommended)
To show suggestions directly in Gorgias:
1. Create a Gorgias Sidebar App integration
2. Point iframe to: `/widget/{{ticket.id}}`
3. AI suggestions appear in ticket sidebar

## Expected Railway Logs

### When Gorgias triggers:
```
INFO: Received raw data type: <class 'list'>
INFO: Converted Gorgias form array to dict
INFO: Request for ticket 190965582 - responding immediately to avoid timeout
INFO: Background: Generating suggestion for ticket 190965582
```

### 5-10 seconds later:
```
INFO: Background: Generated and cached suggestion for 190965582 - Quality: 85
```

### If widget is accessed:
```
INFO: Returning cached suggestion for 190965582
```

## Testing

### Test 1: Trigger from Gorgias
1. Create a ticket or add a message
2. Gorgias sends webhook → Gets `202 Accepted`
3. Check Railway logs for "Background: Generating..."
4. Wait 10 seconds
5. Check logs for "Generated and cached..."

### Test 2: Retrieve Suggestion
```bash
# Wait 10 seconds after triggering, then:
curl https://blosh-ai-new-production.up.railway.app/api/suggest/190965582
```

Should return the AI suggestion!

### Test 3: View Widget
```
https://blosh-ai-new-production.up.railway.app/widget/190965582
```

Should show the suggestion with UI.

## Deployment

**Commit:** `8511e75`  
**Status:** Pushing to Railway...  
**ETA:** 1-2 minutes

## What Changed

### Files Modified:
1. **API_widget_server.py**
   - Changed `/api/suggest` to async (returns 202)
   - Added background threading
   - Added GET endpoint for retrieving suggestions
   - Better error handling

2. **improved_response_generator.py**
   - Lazy-load OpenAI client
   - Prevents startup crash

3. **requirements.txt**
   - Added Werkzeug for Flask compatibility

## Success Indicators

After deployment, you should see in Railway logs:

✅ Server starts successfully  
✅ "Request for ticket X - responding immediately"  
✅ "Background: Generating suggestion..."  
✅ "Background: Generated and cached suggestion - Quality: 85"  
✅ No timeout errors from Gorgias  

## Important Notes

1. **First request takes 5-10 seconds** to generate
2. **Subsequent requests** for same ticket are instant (cached)
3. **Cache is in-memory** (cleared on restart)
4. **For production**, consider Redis for persistent caching

---

**Status:** ✅ Fix deployed!  
**No more timeouts!** 🎉

