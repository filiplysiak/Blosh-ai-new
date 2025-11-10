# Blosh AI Platform

AI-powered customer support automation with Gorgias widget integration.

## Quick Start

### Railway Deployment

1. Deploy: [Railway](https://railway.app) → New Project → Deploy from GitHub
2. Set environment variables:
   ```
   OPENAI_API_KEY=sk-proj-...
   GORGIAS_AUTH=Basic [base64]
   GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
   ```
3. Configure Gorgias widget with Railway URL

### Local Development

```bash
cd Blosh-ai/ai_chats_gorgias/Data_collection_new
pip install -r requirements.txt
python API_widget_server.py
```

See `DEPLOYMENT_SUMMARY.md` for complete details.

## Project Structure

- `Blosh-ai/ai_chats_gorgias/Data_collection_new/` - Widget API (main)
- `Blosh-ai/blosh_platform/` - Platform with brand analyzer
- `Blosh-ai/branche_rapportage/` - Brand report analysis

## Documentation

- `DEPLOYMENT_SUMMARY.md` - Complete deployment guide
- `Blosh-ai/ai_chats_gorgias/Data_collection_new/README.md` - Widget setup details
- `Blosh-ai/blosh_platform/BRAND_ANALYZER_README.md` - Brand analyzer guide

