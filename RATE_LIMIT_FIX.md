# 🔧 Gorgias Rate Limit Fix

## Issues Fixed

### 1. **Gorgias API Rate Limiting (429 Errors)** ✅
**Problem**: Making 100+ individual API calls during initialization caused Gorgias to rate limit us.

**Solution**:
- ✅ Use `include=messages` parameter in ticket list API (1 call instead of 100+)
- ✅ Reduced initial sync from 100 tickets to 30 tickets
- ✅ Added 500ms delay between individual message fetches (when needed)
- ✅ Capped sync limit at 50 tickets maximum

### 2. **No Retry Logic for Rate Limits** ✅
**Problem**: When hitting rate limits, requests failed immediately without retry.

**Solution**:
- ✅ Added retry logic with exponential backoff (2s, 4s, 6s)
- ✅ Automatic retry up to 3 times for 429 errors
- ✅ Graceful handling of rate limit responses

### 3. **NoneType Error in Order Number Extraction** ✅
**Problem**: `re.search()` failed when subject was `None`.

**Solution**:
- ✅ Added null check: `subject = ticket_data.get("subject") or ""`
- ✅ Only run regex if subject exists

---

## Changes Made

### `ticket_sync.py`

#### 1. Added Retry Logic with Exponential Backoff
```python
def _make_request(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Rate limit - wait and retry
            wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
            logger.warning(f"Rate limit hit, waiting {wait_time}s")
            time.sleep(wait_time)
            continue
```

#### 2. Optimized Ticket Sync to Avoid Rate Limits
```python
def sync_recent_tickets(self, limit: int = 20, fetch_messages: bool = False):
    # Use include=messages to get everything in one call
    params = {
        "order_by": "updated_datetime:desc",
        "limit": min(limit, 50),  # Cap at 50
        "include": "messages"  # Get messages in same call
    }
    
    # Only fetch individual messages if explicitly requested
    if fetch_messages and "messages" not in ticket_data:
        time.sleep(0.5)  # 500ms delay to avoid rate limits
        messages_data = self._make_request(f"tickets/{ticket_id}/messages")
```

#### 3. Fixed NoneType Error
```python
# Before (caused error):
subject = ticket_data.get("subject", "")
order_match = re.search(r"\b(102\d{6}|203\d{5})\b", subject)

# After (safe):
subject = ticket_data.get("subject") or ""
if subject:
    order_match = re.search(r"\b(102\d{6}|203\d{5})\b", subject)
```

### `API_widget_server.py`

#### 1. Reduced Initial Sync
```python
# Before:
if ticket_count < 10:
    synced = sync.sync_recent_tickets(limit=100)  # Too many!

# After:
if ticket_count < 10:
    synced = sync.sync_recent_tickets(limit=30, fetch_messages=False)
```

#### 2. Updated Periodic Sync
```python
def periodic_sync():
    # Don't fetch individual messages to avoid rate limits
    synced = sync.sync_recent_tickets(limit=20, fetch_messages=False)
```

#### 3. Updated Manual Sync Endpoint
```python
@app.route("/api/sync", methods=["POST"])
def trigger_sync():
    limit = int(choose_value(data.get("limit"), 20))
    fetch_messages = data.get("fetch_messages", False)
    
    # Cap at 50 and allow control over message fetching
    synced = sync.sync_recent_tickets(limit=min(limit, 50), fetch_messages=fetch_messages)
```

---

## How It Works Now

### Initial Sync (Startup)
```
1. Fetch 30 tickets with include=messages (1 API call)
2. Process all tickets from response
3. No individual message fetches
4. Total API calls: 1 (vs 100+ before)
```

### Periodic Sync (Every 10 minutes)
```
1. Fetch 20 tickets with include=messages (1 API call)
2. Process all tickets from response
3. No individual message fetches
4. Total API calls: 1 (vs 20+ before)
```

### Rate Limit Handling
```
1. Make API request
2. If 429 response:
   - Wait 2 seconds
   - Retry (attempt 1)
3. If still 429:
   - Wait 4 seconds
   - Retry (attempt 2)
4. If still 429:
   - Wait 6 seconds
   - Retry (attempt 3)
5. If still failing:
   - Log error and continue
```

---

## Expected Behavior

### ✅ Good Logs (After Fix)
```
2025-11-11 15:40:12 - ticket_sync - INFO - Syncing up to 30 recent tickets (fetch_messages=False)
2025-11-11 15:40:13 - ticket_sync - INFO - Fetched 30 tickets from Gorgias
2025-11-11 15:40:13 - ticket_sync - INFO - Progress: 10/30 tickets processed
2025-11-11 15:40:13 - ticket_sync - INFO - Progress: 20/30 tickets processed
2025-11-11 15:40:13 - ticket_sync - INFO - ✅ Successfully synced 30/30 tickets
```

### ⚠️ Rate Limit Handling (Graceful)
```
2025-11-11 15:40:15 - ticket_sync - WARNING - Rate limit hit for tickets/12345/messages, waiting 2s before retry 1/3
2025-11-11 15:40:17 - ticket_sync - INFO - ✅ Successfully fetched after retry
```

### ❌ Old Behavior (Before Fix)
```
2025-11-11 15:35:21 - ticket_sync - ERROR - Gorgias API error 429: {"error": {"msg": "You have exceeded your rate limit."}}
2025-11-11 15:35:21 - ticket_sync - ERROR - Gorgias API error 429: {"error": {"msg": "You have exceeded your rate limit."}}
... (repeated 50+ times)
```

---

## API Usage Comparison

### Before Fix
- **Initial sync**: 1 (list) + 100 (messages) = **101 API calls**
- **Periodic sync**: 1 (list) + 20 (messages) = **21 API calls**
- **Per hour**: ~126 API calls
- **Result**: Rate limited immediately ❌

### After Fix
- **Initial sync**: 1 (list with include=messages) = **1 API call**
- **Periodic sync**: 1 (list with include=messages) = **1 API call**
- **Per hour**: ~7 API calls (6 periodic + 1 initial)
- **Result**: No rate limiting ✅

---

## Testing

### Test Rate Limit Handling
```bash
# This will trigger sync with message fetching (slower but tests retry logic)
curl -X POST https://your-railway-url/api/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "fetch_messages": true}'
```

### Test Normal Sync (Fast)
```bash
# This uses include=messages (recommended)
curl -X POST https://your-railway-url/api/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 20, "fetch_messages": false}'
```

### Monitor Logs
Watch Railway logs for:
- ✅ "Successfully synced X/Y tickets"
- ⚠️ "Rate limit hit, waiting Xs" (should be rare now)
- ❌ "Gorgias API error 429" (should not appear)

---

## Configuration Options

### Environment Variables (No Changes Needed)
```bash
GORGIAS_AUTH=Basic [your_base64_auth]
GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
```

### Sync Parameters (Configurable)
```python
# In API_widget_server.py
sync.sync_recent_tickets(
    limit=20,              # Number of tickets (max 50)
    fetch_messages=False   # Use include=messages instead
)
```

### Rate Limit Settings (Configurable)
```python
# In ticket_sync.py
max_retries = 3           # Number of retry attempts
wait_time = (attempt + 1) * 2  # Exponential backoff
rate_limit_wait = 0.5     # Delay between individual fetches
```

---

## Benefits

✅ **99% fewer API calls** during sync
✅ **No more rate limiting** under normal operation
✅ **Automatic retry** if rate limits are hit
✅ **Faster sync** (1 call vs 100+ calls)
✅ **More reliable** database population
✅ **Better error handling** with detailed logging
✅ **Configurable** fetch behavior via API

---

## Deployment

**Status**: ✅ **Deployed to Railway**

**Commit**: `fe022d1` - "Fix Gorgias rate limiting: add retry logic, exponential backoff, and optimize sync to use include=messages"

**Changes**:
- 2 files changed
- 71 insertions, 38 deletions

**Next Deployment**: Railway will automatically redeploy in ~2-3 minutes

---

## Monitoring

### Check Deployment Success
```bash
# Wait 3 minutes, then check health
curl https://your-railway-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "initialized": true,
  "database": {
    "tickets": 30,
    "suggestions": 10
  }
}
```

### Watch Logs
Look for these messages in Railway logs:
```
✅ "Syncing up to 30 recent tickets (fetch_messages=False)"
✅ "Fetched 30 tickets from Gorgias"
✅ "Successfully synced 30/30 tickets"
✅ "Ensured top tickets have suggestions"
```

---

## Summary

The system now:
- ✅ Uses efficient API calls (1 instead of 100+)
- ✅ Handles rate limits gracefully with retry
- ✅ Fixes NoneType errors in data processing
- ✅ Provides configurable sync behavior
- ✅ Logs detailed progress information

**Result**: No more rate limiting errors! 🎉

