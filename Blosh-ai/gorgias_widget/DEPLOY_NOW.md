# Deploy Gorgias Widget - SIMPLE 3-STEP PROCESS

## WHY WE NEED THIS:

Gorgias (in the cloud) → Needs to call → Your API (to get AI suggestions)

Your PC isn't public, so we deploy to Railway (free hosting).

```
Gorgias ──→ Railway (your API) ──→ OpenAI (fine-tuned model) ──→ AI Suggestion
```

---

## STEP 1: Deploy to Railway (3 minutes)

1. **Go to:** https://railway.app/

2. **Click:** "Start a New Project"

3. **Click:** "Deploy from GitHub repo"

4. **Select:** `Blosh-ai` repository

5. **Important Settings:**
   - **Root Directory:** `gorgias_widget`
   - **Start Command:** (leave default, Procfile will handle it)

6. **Click Deploy**

7. **Wait 2 minutes** for deployment to finish

8. **Copy the URL** that Railway gives you
   - Will look like: `https://blosh-ai-production.up.railway.app`

---

## STEP 2: Tell Me the URL

**Just paste your Railway URL here in the chat!**

Example: `https://blosh-ai-production.up.railway.app`

---

## STEP 3: I'll Create the Widget

Once you give me the URL, I will automatically:
- ✅ Update create_widget.py with your URL
- ✅ Run the script to create the widget in Gorgias
- ✅ Widget appears in your sidebar!

---

## That's It!

**Total Time:** 5 minutes  
**Cost:** FREE  
**Result:** AI suggestions in Gorgias sidebar

---

## Why Railway Instead of Your PC?

| Your PC (with ngrok) | Railway |
|---------------------|---------|
| ❌ Requires ngrok account | ✅ No extra accounts |
| ❌ PC must stay on | ✅ Always available |
| ❌ Slow if PC sleeps | ✅ Fast & reliable |
| ❌ New URL each restart | ✅ Permanent URL |

---

**Ready? Go to Step 1 above!**

Once you paste your Railway URL, I'll finish the rest automatically!

