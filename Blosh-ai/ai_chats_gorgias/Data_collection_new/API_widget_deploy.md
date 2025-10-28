# Deploy Gorgias Widget API

## Quick Deploy to Railway (5 minutes)

1. **Go to Railway:** https://railway.app/
2. **New Project** → Deploy from GitHub repo
3. **Add environment variables:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   
   GORGIAS_AUTH=your_gorgias_basic_auth_here
   
   GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
   
   PORT=5000
   ```

4. **Create `Procfile`** in your repo root:
   ```
   web: gunicorn API_widget_server:app --workers 2 --bind 0.0.0.0:$PORT
   ```

5. **Deploy!** Railway will auto-deploy

6. **Copy your URL** (e.g., `https://your-app.railway.app`)

---

## Configure Gorgias Widget

1. **Go to Gorgias:** Settings → App Store → Widgets

2. **Add Widget:**
   - Name: `AI Response Suggestion`
   - URL: `https://your-app.railway.app/widget/{{ticket.id}}`
   - Location: `Ticket Sidebar`
   - Size: `Medium`
   - When to show: `Ticket is open`

3. **Save**

---

## Test

1. Open any ticket in Gorgias
2. Check the sidebar
3. You should see the AI suggestion widget!

---

## Endpoints

- `GET /health` - Check if server is running
- `POST /api/suggest` - Generate AI suggestion (JSON: `{"ticket_id": "123"}`)
- `GET /widget/{ticket_id}` - Widget interface (used by Gorgias)
- `POST /api/feedback` - Record agent feedback

---

## Test Locally

```bash
# Install dependencies
pip install -r API_widget_requirements.txt

# Run server
python API_widget_server.py

# Test
curl http://localhost:5000/health
```

Then open: `http://localhost:5000/widget/test123`

