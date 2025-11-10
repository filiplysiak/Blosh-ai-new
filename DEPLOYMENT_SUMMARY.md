# Blosh AI - Deployment Summary

## Widget API Status

**Deployed to Railway**: ✅ Active  
**Fine-tuned Model**: `ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB`  
**Quality Score**: 70-80% excellent responses

---

## Environment Variables (Railway)

```
OPENAI_API_KEY=sk-proj-...
GORGIAS_AUTH=Basic [base64_encoded]
GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/suggest` | POST | Generate AI suggestion |
| `/api/suggest/<id>` | GET | Get cached suggestion |
| `/widget/<id>` | GET, POST | Widget HTML (GET) or trigger generation (POST) |
| `/api/feedback` | POST | Record feedback |

---

## Local Development

```bash
# Set environment variables
export OPENAI_API_KEY="sk-proj-..."
export GORGIAS_AUTH="Basic ..."

# Install dependencies
cd Blosh-ai/ai_chats_gorgias/Data_collection_new
pip install -r requirements.txt

# Run server
python API_widget_server.py

# Optional: Expose with ngrok
ngrok http 5000
```

---

## Railway Deployment

```bash
# Deploy via GitHub
git push origin main

# Or via Railway CLI
railway up
```

**Procfile**: `web: cd Blosh-ai/ai_chats_gorgias/Data_collection_new && gunicorn API_widget_server:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120`

---

## Gorgias Widget Configuration

```html
<iframe 
  src="https://[your-railway-url]/widget/{{ticket.id}}" 
  width="100%" 
  height="700px" 
  frameborder="0"
></iframe>
```

---

## Key Features

- ✅ Async processing (avoids 5s timeout)
- ✅ Handles multiple Gorgias data formats
- ✅ Brand detection (Freebird/Simple)
- ✅ Quality scoring and validation
- ✅ Auto-fixes common issues
- ✅ In-memory caching
- ✅ Feedback tracking

---

## Cost Estimate

- **Railway**: $5-20/month
- **OpenAI API**: $9-45/month (usage-based)
- **Total**: $14-65/month

---

## Performance

- Initial response: < 500ms
- AI generation: 5-10s (background)
- Widget load: < 1s
- Quality: 70-80% high-quality responses

