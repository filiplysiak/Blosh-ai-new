# Deploy Gorgias API Fix to Railway

## What Was Fixed
Fixed the `AttributeError: 'list' object has no attribute 'get'` error by making the API handle both dictionary and list formats from Gorgias.

## Files Changed
- ✅ `API_widget_server.py` - Updated `/api/suggest` and `/api/feedback` endpoints

## Deployment Steps

### Option 1: Automatic Deployment (Recommended)
If your Railway project is connected to GitHub:

1. **Commit and push the changes:**
   ```bash
   cd Blosh-ai-new
   git add .
   git commit -m "Fix: Handle list format from Gorgias API webhooks"
   git push origin main
   ```

2. **Railway will automatically deploy** the changes
   - Check the Railway dashboard for deployment status
   - Wait for "Deployed" status (usually 1-2 minutes)

3. **Verify in Railway logs:**
   - Go to Railway dashboard → Your project → Logs
   - Look for: `"Received raw data type: <class 'list'>"`
   - Look for: `"Extracted data from list format"`
   - Should see: `"Generating suggestion for ticket XXXXX"`

### Option 2: Manual Deployment
If not connected to GitHub:

1. **Login to Railway:**
   ```bash
   railway login
   ```

2. **Link to your project:**
   ```bash
   railway link
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

## Testing After Deployment

### 1. Test Health Endpoint
```bash
curl https://your-railway-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T..."
}
```

### 2. Test with Gorgias Widget
- Open a ticket in Gorgias
- The AI widget should now load without errors
- Check Railway logs for successful processing

### 3. Monitor Logs
In Railway dashboard, watch for:
```
✅ Received raw data type: <class 'list'>
✅ Extracted data from list format
✅ Generating suggestion for ticket 123456
✅ Generated suggestion for 123456 - Quality: 85
```

### 4. Run Test Script (Optional)
Update `test_api_formats.py` with your Railway URL:
```python
BASE_URL = "https://your-railway-app.railway.app"
```

Then run:
```bash
python test_api_formats.py
```

## Environment Variables
Make sure these are set in Railway:

- ✅ `OPENAI_API_KEY` - Your OpenAI API key
- ✅ `GORGIAS_AUTH` - Gorgias authentication token
- ✅ `GORGIAS_BASE_URL` - `https://freebirdicons.gorgias.com/api`
- ✅ `PORT` - (Auto-set by Railway)

## Troubleshooting

### Still Getting Errors?
1. **Check Railway logs** for the exact error
2. **Verify environment variables** are set correctly
3. **Check Gorgias webhook configuration**
4. **Test with curl:**
   ```bash
   curl -X POST https://your-railway-app.railway.app/api/suggest \
     -H "Content-Type: application/json" \
     -d '[{"ticket_id": "123456"}]'
   ```

### Logs Show "Invalid data format"?
The API is receiving data in an unexpected format. Check Railway logs for:
```
Received raw data: [actual data here]
```

### No Logs Appearing?
- Gorgias webhook might not be configured correctly
- Check Gorgias webhook URL points to your Railway app
- Verify webhook is enabled in Gorgias settings

## Success Indicators
✅ No more `AttributeError` in logs  
✅ Logs show "Extracted data from list format"  
✅ AI suggestions appear in Gorgias widget  
✅ Quality scores are displayed  
✅ Copy/Use buttons work  

## Rollback (If Needed)
If something goes wrong:
```bash
git revert HEAD
git push origin main
```

Railway will automatically redeploy the previous version.

## Support
If issues persist:
1. Check Railway logs for detailed error messages
2. Verify all environment variables are set
3. Test the health endpoint first
4. Use the test script to isolate the issue

---
**Deployed:** November 10, 2025  
**Status:** Ready for production ✅

