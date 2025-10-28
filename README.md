# Blosh AI Platform

AI-powered platform with Gorgias widget integration for automated customer support.

## 🚀 Quick Deploy to Railway

### 1. Deploy on Railway

1. Go to [Railway](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select this repository: `filiplysiak/Blosh-ai-new`
4. Railway will auto-detect the configuration

### 2. Configure Environment Variables

Add these environment variables in Railway:

```bash
OPENAI_API_KEY=your_openai_api_key_here
GORGIAS_AUTH=your_gorgias_basic_auth_credentials
GORGIAS_BASE_URL=https://freebirdicons.gorgias.com/api
PORT=5000
```

### 3. Choose Which Service to Deploy

This repository contains multiple services. Railway will look for a `Procfile` to know what to run. 

**For Gorgias Widget API:**
- Use the Procfile in `Blosh-ai/ai_chats_gorgias/Data_collection_new/`
- Or manually set the start command to:
  ```
  cd Blosh-ai/ai_chats_gorgias/Data_collection_new && pip install -r API_widget_requirements.txt && python API_widget_server.py
  ```

### 4. Deploy!

Railway will automatically deploy your application. Once deployed, you'll get a URL like:
```
https://your-app.railway.app
```

### 5. Configure Gorgias Widget

1. Go to Gorgias: **Settings → App Store → Widgets**
2. Add a new widget:
   - **Name**: AI Response Suggestion
   - **URL**: `https://your-app.railway.app/widget/{{ticket.id}}`
   - **Location**: Ticket Sidebar
   - **Size**: Medium
   - **Show when**: Ticket is open

3. Save and test!

## 📂 Project Structure

- **`Blosh-ai/ai_chats_gorgias/`** - Gorgias integration & AI response generator
- **`Blosh-ai/gorgias_widget/`** - Alternative widget implementation
- **`Blosh-ai/blosh_platform/`** - Full platform with brand analyzer
- **`Blosh-ai/branche_rapportage/`** - Brand report analysis tools

## 🔧 Local Development

### Test Gorgias Widget Locally

```bash
cd Blosh-ai/ai_chats_gorgias/Data_collection_new

# Install dependencies
pip install -r API_widget_requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export GORGIAS_AUTH="your-auth"

# Run server
python API_widget_server.py
```

Then visit: `http://localhost:5000/health`

## 📚 Documentation

- [API Widget Deploy Guide](Blosh-ai/ai_chats_gorgias/Data_collection_new/API_widget_deploy.md)
- [API Widget Setup](Blosh-ai/ai_chats_gorgias/Data_collection_new/API_widget_setup.md)
- [Brand Analyzer README](Blosh-ai/blosh_platform/BRAND_ANALYZER_README.md)

## 🔐 Security

⚠️ **Important**: Never commit API keys or credentials to the repository. Always use environment variables.

## 📞 Support

For issues or questions, contact the development team.

---

**Repository**: https://github.com/filiplysiak/Blosh-ai-new

