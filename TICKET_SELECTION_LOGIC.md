# 📋 Ticket Selection Logic

## How Tickets Are Added to Database

### ✅ **Current Logic (What You Want!)**

Tickets are selected based on **`updated_datetime`** (last activity), NOT creation date.

```python
# In ticket_sync.py
params = {
    "order_by": "updated_datetime:desc",  # Most recently UPDATED first
    "limit": 10
}
```

### **What This Means**

✅ **Old tickets with new responses** → Get synced
✅ **Recently updated tickets** → Get synced
✅ **Tickets with recent customer messages** → Get synced
✅ **Tickets with recent agent replies** → Get synced
❌ **Old tickets with no activity** → NOT synced

### **Example Scenarios**

| Ticket | Created | Last Updated | Will Sync? |
|--------|---------|--------------|------------|
| Ticket A | 2 months ago | 5 minutes ago (new reply) | ✅ YES |
| Ticket B | Yesterday | Yesterday | ✅ YES |
| Ticket C | 1 week ago | 1 week ago (no activity) | ❌ NO |
| Ticket D | Today | Today | ✅ YES |

---

## 🔄 **Sync Frequency**

### **Initial Sync (On Startup)**
```python
if ticket_count < 10:
    sync.sync_recent_tickets(limit=10)  # Sync 10 most recently updated
else:
    sync.sync_recent_tickets(limit=5)   # Sync 5 most recently updated
```

### **Periodic Sync (Every 10 Minutes)**
```python
sync.sync_recent_tickets(limit=5)  # Sync 5 most recently updated
```

### **Manual Sync (Via API)**
```bash
curl -X POST https://your-url/api/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}'  # Sync up to 20 (max 50)
```

---

## 🎯 **Which Tickets Get AI Suggestions**

After syncing, the system generates suggestions for:

1. **Top 10 most recent tickets** (by `updated_datetime`)
2. **Tickets with customer messages** (skips empty tickets)
3. **Email tickets** (prioritized for AI suggestions)

```python
# In suggestion_manager.py
def ensure_suggestions_for_top_n(n=10):
    # Get top N most recent tickets
    recent_tickets = db.get_recent_tickets(limit=n)
    
    for ticket in recent_tickets:
        # Skip if already has suggestion
        if db.has_suggestion(ticket_id):
            continue
        
        # Skip if no customer message
        if not ticket['last_customer_message']:
            continue
        
        # Queue for generation with high priority
        queue_generation(ticket_id, priority=10)
```

---

## 📊 **Database Query**

```sql
-- How tickets are retrieved for suggestions
SELECT * FROM tickets 
ORDER BY updated_at DESC  -- Most recently updated first
LIMIT 10;

-- NOT this:
SELECT * FROM tickets 
ORDER BY created_at DESC  -- Would prioritize new tickets only
LIMIT 10;
```

---

## 🧹 **Test Data Issue**

### **Problem**
Test tickets (`test_12345`, `test_gen_123`) were created during development and are still in the database.

### **Solution**
Clean them up via API:

```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/cleanup-test-data
```

Response:
```json
{
  "status": "success",
  "message": "Removed 2 test tickets",
  "deleted": {
    "tickets": 2,
    "suggestions": 2,
    "queue": 1,
    "feedback": 0
  },
  "test_tickets_removed": ["test_12345", "test_gen_123"]
}
```

---

## 🔍 **Verification**

### **Check What's Being Synced**
```bash
curl https://blosh-ai-new-production.up.railway.app/api/stats
```

Look at `top_tickets` - these are ordered by `updated_at`:
```json
{
  "top_tickets": [
    {
      "ticket_id": "12345678",
      "created_at": "2025-10-15T10:00:00",  // Created long ago
      "updated_at": "2025-11-11T15:30:00",  // Updated recently ← This is what matters!
      "subject": "Follow-up question",
      "has_suggestion": true
    }
  ]
}
```

### **Check Sync Logs**
In Railway logs, look for:
```
2025-11-11 15:40:00 - ticket_sync - INFO - Syncing up to 10 recent tickets
2025-11-11 15:40:01 - ticket_sync - INFO - Fetched 10 tickets from Gorgias
```

These are the 10 most recently **updated** tickets from Gorgias.

---

## ✅ **Summary**

Your system **already works the way you want**:

1. ✅ Tickets sorted by **update time** (not creation time)
2. ✅ Old tickets with new activity **get synced**
3. ✅ Top 10 most recently updated tickets **get suggestions**
4. ✅ Syncs every 10 minutes to catch new activity

**Only issue**: Test data needs cleanup (fixed with new endpoint)

---

## 🚀 **Action Items**

1. **Clean up test data**:
   ```bash
   curl -X POST https://blosh-ai-new-production.up.railway.app/api/cleanup-test-data
   ```

2. **Verify clean data**:
   ```bash
   curl https://blosh-ai-new-production.up.railway.app/api/suggestions
   ```
   Should show only real Gorgias tickets (no "Test Customer")

3. **Check ticket selection**:
   ```bash
   curl https://blosh-ai-new-production.up.railway.app/api/stats
   ```
   Verify `top_tickets` are the most recently updated ones

---

## 📖 **Code Reference**

### Ticket Sync (`ticket_sync.py`)
```python
def sync_recent_tickets(self, limit: int = 20):
    params = {
        "order_by": "updated_datetime:desc",  # ← Key line!
        "limit": min(limit, 50)
    }
    response = self._make_request("tickets", params=params)
```

### Database Retrieval (`database.py`)
```python
def get_recent_tickets(self, limit: int = 10):
    cursor.execute("""
        SELECT * FROM tickets 
        ORDER BY updated_at DESC  # ← Sorted by update time
        LIMIT ?
    """, (limit,))
```

### Suggestion Generation (`suggestion_manager.py`)
```python
def ensure_suggestions_for_top_n(self, n: int = 10):
    # Gets top N by updated_at (most recent activity)
    recent_tickets = self.db.get_recent_tickets(limit=n)
```

