# Gorgias HTML Widget Setup Guide

## Overview
This guide shows you how to add an AI response suggestion widget to your Gorgias sidebar using Custom HTML Widgets.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  GORGIAS TICKET SIDEBAR                         │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Custom HTML Widget (iframe)               │ │
│  │                                            │ │
│  │  https://your-api.railway.app/widget/123  │ │
│  │                                            │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │  🤖 AI Suggestion                    │ │ │
│  │  │  Quality: 85% (High)                 │ │ │
│  │  │                                      │ │ │
│  │  │  [Suggestion text here...]           │ │ │
│  │  │                                      │ │ │
│  │  │  [✓ Use Response]  [📋 Copy]        │ │ │
│  │  └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         ↓ Widget makes API call
┌─────────────────────────────────────────────────┐
│  YOUR API SERVER                                 │
│  POST /api/suggest                               │
│  → Fetches ticket from Gorgias API              │
│  → Generates AI suggestion                       │
│  → Returns response                              │
└─────────────────────────────────────────────────┘
         ↓ Calls OpenAI
┌─────────────────────────────────────────────────┐
│  OPENAI FINE-TUNED MODEL                        │
│  ft:gpt-4.1-mini-2025-04-14:personal:blosh:...  │
└─────────────────────────────────────────────────┘
```

---

## Step 1: Deploy Your API Server

### Option A: Railway (Recommended - Free Tier)

1. **Go to:** https://railway.app/

2. **Sign up** with GitHub

3. **New Project** → "Deploy from GitHub repo"

4. **Select your repository:** `Blosh-ai`

5. **Set start command** (in Railway settings):
   ```
   cd ai_chats_gorgias/Data_collection_new && gunicorn API_widget_server:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120
   ```

6. **Add environment variables:**
   - `OPENAI_API_KEY` = (already in code)
   - `GORGIAS_AUTH` = (already in code)
   - `GORGIAS_BASE_URL` = `https://freebirdicons.gorgias.com/api`
   - `PORT` = `5000`

7. **Deploy!** Wait 2-3 minutes

8. **Copy your URL:** e.g., `https://blosh-ai-production.up.railway.app`

### Option B: Local Testing

```bash
cd ai_chats_gorgias/Data_collection_new
pip install -r API_widget_requirements.txt
python API_widget_server.py
```

Then use ngrok to expose it:
```bash
ngrok http 5000
```

---

## Step 2: Test Your API

Before configuring Gorgias, test that your API works:

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Should return: {"status":"healthy","timestamp":"..."}

# Test widget HTML (in browser)
# Open: https://your-app.railway.app/widget/test123
```

---

## Step 3: Configure Gorgias Widget

### Method 1: Using Custom HTTP Widget (Recommended)

1. **Go to Gorgias:** Settings → App Store → Widgets

2. **Find "Standalone" widget** at the bottom of the page

3. **Drag it** to your ticket sidebar layout

4. **Click the settings icon** on the widget

5. **Configure:**
   - **Widget Title:** `🤖 AI Response Suggestion`
   - **Widget Type:** `Custom HTTP Widget`

6. **Add HTTP Integration:**
   - Click "Add HTTP Integration"
   - **Name:** `AI Suggestion API`
   - **Method:** `POST`
   - **URL:** `https://your-app.railway.app/api/suggest`
   - **Headers:**
     ```
     Content-Type: application/json
     ```
   - **Body:**
     ```json
     {
       "ticket_id": "{{ticket.id}}"
     }
     ```
   - **Save**

7. **Display fields:**
   - Drag "suggestion" field to display
   - Drag "quality_score" field to display
   - Drag "brand" field to display

### Method 2: Using iframe Widget (Alternative)

If Method 1 doesn't work, you can use an iframe:

1. **Go to:** Settings → Widgets

2. **Add Custom Widget**

3. **Widget Type:** `Custom HTML`

4. **HTML Code:**
   ```html
   <iframe 
     src="https://your-app.railway.app/widget/{{ticket.id}}" 
     width="100%" 
     height="600px" 
     frameborder="0"
     style="border: none;"
   ></iframe>
   ```

5. **When to show:**
   - Ticket is open
   - Ticket has customer messages

6. **Save Changes**

---

## Step 4: Test in Gorgias

1. **Open any ticket** in Gorgias

2. **Check the sidebar** on the right

3. **You should see:**
   - Widget loading spinner
   - AI-generated suggestion appears
   - Quality score badge
   - Brand tag (Freebird/Simple)
   - Copy and Use buttons

4. **Test the buttons:**
   - Click "Copy" → Should copy to clipboard
   - Click "Use Response" → Should copy and mark as used
   - Click feedback buttons → Records your feedback

---

## Troubleshooting

### Widget shows "Loading..." forever

**Check:**
1. Is your API running? Test: `curl https://your-api.com/health`
2. Check Railway logs for errors
3. Open browser console (F12) and check for JavaScript errors

**Fix:**
- Verify CORS is enabled (already in code)
- Check ticket has messages
- Try with a different ticket

### "No message found" error

**Check:**
1. Ticket has customer messages (not just agent notes)
2. Gorgias API returns message data

**Fix:**
- The API will automatically fetch ticket data from Gorgias
- Make sure GORGIAS_AUTH is correct

### Quality score is always low

**Check:**
- Review the warnings shown in widget
- Check if customer name is detected
- Verify order number extraction

**Fix:**
- See `IMPROVE_WITHOUT_RETRAINING.md` for optimization tips
- Adjust system prompts in `improved_response_generator.py`

### Widget not appearing

**Check:**
1. Widget is enabled in Gorgias settings
2. Widget visibility conditions match your ticket
3. Sidebar layout has space for widget

**Fix:**
- Go to Settings → Widgets
- Check "When to show" conditions
- Drag widget higher in layout

---

## Widget Features

✅ **Auto-loads** when ticket opens  
✅ **Real-time generation** from fine-tuned model  
✅ **Quality scoring** (High/Medium/Low confidence)  
✅ **Brand detection** (Freebird vs Simple)  
✅ **Copy to clipboard** button  
✅ **Use response** button (copies + records feedback)  
✅ **Feedback tracking** (Used/Edited/Ignored)  
✅ **Warnings display** for low quality  
✅ **Caching** for faster repeat loads  
✅ **Beautiful UI** matches Gorgias style  

---

## API Endpoints

Your deployed API has these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/suggest` | POST | Generate AI suggestion |
| `/widget/{ticket_id}` | GET | HTML widget interface |
| `/api/feedback` | POST | Record agent feedback |

---

## Advanced Configuration

### Change Widget Appearance

Edit the CSS in `API_widget_server.py` around line 250:

```css
/* Change primary color */
.btn-primary {
    background: #your-color;
}

/* Adjust widget height */
.suggestion-text {
    max-height: 600px;  /* Increase for longer messages */
}
```

### Add More Action Buttons

In the HTML section, add buttons:

```html
<button class="btn btn-secondary" onclick="editResponse()">
    ✏️ Edit & Use
</button>
```

Then add JavaScript function:

```javascript
function editResponse() {
    // Your logic here
}
```

### Track More Metrics

Modify `/api/feedback` endpoint to store in database:

```python
@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    data = request.get_json()
    # TODO: Store in PostgreSQL/MongoDB
    # db.feedback.insert(data)
    return jsonify({'status': 'success'})
```

---

## Monitoring

### Check API Logs (Railway)

1. Go to Railway dashboard
2. Select your project
3. Click "Logs" tab
4. Watch for errors or slow requests

### Monitor Performance

Key metrics to track:
- **Response time:** Should be < 3 seconds
- **Cache hit rate:** Higher is better
- **Quality scores:** Average should be > 70%
- **Usage rate:** % of suggestions actually used

---

## Cost Estimate

**Railway Hosting:** $0-5/month (free tier covers most usage)  
**OpenAI API:** ~$0.0003 per suggestion  
- 100 suggestions/day = $9/month  
- 500 suggestions/day = $45/month  

**Total:** < $50/month for most use cases

---

## Next Steps

After deployment:

1. ✅ Test with 10-20 tickets
2. ✅ Gather agent feedback
3. ✅ Review quality scores
4. ✅ Optimize prompts (see `IMPROVE_WITHOUT_RETRAINING.md`)
5. ✅ Monitor usage and costs
6. ✅ Iterate based on feedback

---

## Support

**Issues with deployment?**
- Check Railway logs
- Test API endpoints with curl
- Review browser console for errors

**Issues with suggestions?**
- See `IMPROVE_WITHOUT_RETRAINING.md`
- Review `RESPONSE_QUALITY_ANALYSIS.md`
- Adjust system prompts in code

**Need help?**
- Review this guide again
- Check Gorgias documentation
- Test each component separately

---

**You're ready to deploy! Follow the steps above to get your AI widget live in Gorgias.** 🚀

