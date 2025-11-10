# Gorgias AI Widget Setup Guide

Complete guide to integrate the AI response suggestion widget with your Gorgias account.

---

## 🚀 Quick Setup (5 minutes)

### Railway Deployment URL
```
https://blosh-ai-new-production.up.railway.app
```

### Step 1: Create Widget in Gorgias

1. **Login to Gorgias**: Go to your Gorgias admin panel
2. **Navigate to**: Settings → Productivity → Widgets
3. **Click**: "+ Add Widget" or "Create Widget"

### Step 2: Configure Widget

**Widget Type**: Choose **"Custom HTML"** or **"HTTP Integration"**

#### Option A: Custom HTML Widget (Recommended)

**Widget Configuration:**
- **Name**: `AI Response Suggestion`
- **Type**: `Custom HTML`
- **Position**: `Right Sidebar` (Ticket view)
- **HTML Code**:

```html
<iframe 
  src="https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}" 
  width="100%" 
  height="700px" 
  frameborder="0"
  style="border: none; min-height: 700px;"
></iframe>
```

**Display Conditions:**
- ✅ Ticket is open
- ✅ Ticket has customer message (optional but recommended)

#### Option B: HTTP Integration Widget

**Widget Configuration:**
- **Name**: `AI Response Suggestion`
- **Type**: `HTTP Integration`
- **Position**: `Right Sidebar` (Ticket view)
- **HTTP Method**: `GET`
- **URL**: `https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}`
- **Headers**: Leave empty (CORS is configured)

**Display Fields** (if using HTTP integration):
- The widget will render its own HTML interface automatically

### Step 3: Save and Enable

1. Click **"Save"** or **"Create"**
2. Ensure the widget is **Enabled** (toggle should be ON)
3. Drag the widget to your preferred position in the sidebar

---

## ✅ Testing

### Test the Widget

1. **Open any ticket** in Gorgias with a customer message
2. **Check the right sidebar** - you should see "🤖 AI Suggestion"
3. **Widget behavior**:
   - If suggestion exists: Shows immediately
   - If not: Shows "Generate response" button
   - Click "Generate response": Shows loading spinner → displays AI suggestion (5-10s)

### Test the Buttons

- **"Use response"**: Copies suggestion to clipboard + shows toast notification
- **"Copy"**: Copies suggestion to clipboard
- **"Regenerate"**: Generates a new suggestion
- **Feedback buttons** (👍 Used / ✏️ Edited / 👎 Ignored): Records your feedback

### Expected Behavior

✅ Widget loads inline (no new tabs/windows)  
✅ Shows loading spinner while generating  
✅ Displays suggestion with quality score and brand  
✅ Copy/paste works from clipboard  
✅ Multiple tickets can have widgets open simultaneously  

---

## 🔧 Advanced Configuration

### Custom Display Conditions

You can configure when the widget appears:

**Show only for specific channels:**
```
Ticket channel is email
OR Ticket channel is chat
```

**Show only for specific tags:**
```
Ticket has tag "needs-ai-help"
```

**Hide for closed tickets:**
```
Ticket status is NOT closed
```

### Widget Positioning

Drag the widget in the Gorgias sidebar editor to position it:
- **Top**: Most visible, agents see it first
- **Middle**: Balanced with other widgets
- **Bottom**: Less intrusive

---

## 🐛 Troubleshooting

### Widget Not Appearing

**Check:**
1. Widget is **Enabled** in Gorgias Settings → Widgets
2. Display conditions are met (ticket is open, has message, etc.)
3. Clear browser cache and refresh Gorgias

### Widget Shows "Loading..." Forever

**Possible causes:**
1. **Railway deployment is down**: Check https://blosh-ai-new-production.up.railway.app/health
2. **Environment variables missing**: Verify in Railway dashboard:
   - `OPENAI_API_KEY`
   - `GORGIAS_AUTH`
   - `GORGIAS_BASE_URL`
3. **Check Railway logs**: Railway dashboard → Deployments → View logs

### "No message found" Error

**Cause**: Ticket doesn't have a customer message yet

**Solution**: Wait for customer to send a message, or check that `GORGIAS_AUTH` is correctly formatted:
```
Basic [base64_encoded_email:api_key]
```

### Suggestion Generation Fails

**Check Railway logs** for errors:
```bash
# View logs in Railway dashboard
# Or use Railway CLI:
railway logs
```

**Common issues:**
- OpenAI API key invalid or expired
- Gorgias API authentication failed
- Network timeout (increase Railway timeout if needed)

### Widget Shows Old/Cached Suggestions

**Solution**: Click "Regenerate" button in the widget

**Or**: Clear the database cache via API:
```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/init
```

---

## 📊 Monitoring

### Health Check

Check if the service is running:
```bash
curl https://blosh-ai-new-production.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T...",
  "initialized": true,
  "database": {
    "total_tickets": 150,
    "tickets_with_suggestions": 85,
    "coverage_percentage": 56.7
  }
}
```

### Statistics

View database statistics:
```bash
curl https://blosh-ai-new-production.up.railway.app/api/stats
```

### Manual Sync

Trigger a manual ticket sync:
```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}'
```

---

## 🔐 Security

### CORS Configuration

The API is configured to accept requests from:
- `https://*.gorgias.com`
- `https://freebirdicons.gorgias.com`

### Authentication

- **Gorgias → Railway**: No auth required (CORS-protected)
- **Railway → Gorgias API**: Uses `GORGIAS_AUTH` environment variable
- **Railway → OpenAI**: Uses `OPENAI_API_KEY` environment variable

### Data Storage

- All tickets and suggestions are stored in SQLite database
- Database location: `/data/widget.db` (or `WIDGET_DB_PATH` env var)
- No sensitive customer data is sent to OpenAI (only message content for generation)

---

## 📈 Performance

### Expected Timings

- **Widget load**: < 1 second
- **Cached suggestion**: < 500ms
- **New suggestion generation**: 5-10 seconds
- **Background pre-generation**: Runs every 5 minutes for top 10 tickets

### Optimization Tips

1. **Pre-generation**: The system automatically pre-generates suggestions for the 10 most recent tickets
2. **Caching**: Once generated, suggestions are cached in the database
3. **Concurrent requests**: Multiple agents can use the widget simultaneously

---

## 🆘 Support

### Check Railway Logs

```bash
# In Railway dashboard:
# Project → Deployments → View Logs

# Or via CLI:
railway logs --tail
```

### Common Log Messages

✅ **Good:**
```
🚀 Initializing widget backend
✅ Initialization complete
Synced 20 tickets during initialization
Generated suggestion for ticket 12345 - Quality: 85%
```

❌ **Issues:**
```
OPENAI_API_KEY not set
GORGIAS_AUTH not configured
Error generating suggestion: ...
```

### Need Help?

1. Check Railway deployment status
2. Verify environment variables are set correctly
3. Review Railway logs for specific errors
4. Test the health endpoint: `/health`

---

## 📝 Notes

- The widget uses the fine-tuned model: `ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB`
- Quality scores: 70%+ = High, 50-69% = Medium, <50% = Low
- Brand detection: Automatically detects Freebird Icons vs Simple the Brand
- Feedback tracking: All button clicks are logged for future analytics

---

## 🎯 Next Steps

After setup:
1. ✅ Test with a few tickets
2. ✅ Train your team on how to use the widget
3. ✅ Monitor quality scores and feedback
4. ✅ Adjust display conditions if needed
5. ✅ Review Railway usage and costs

---

**Deployment URL**: https://blosh-ai-new-production.up.railway.app  
**Health Check**: https://blosh-ai-new-production.up.railway.app/health  
**Stats**: https://blosh-ai-new-production.up.railway.app/api/stats

