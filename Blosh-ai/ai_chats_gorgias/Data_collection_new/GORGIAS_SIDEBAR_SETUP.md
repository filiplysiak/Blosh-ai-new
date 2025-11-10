# How to See AI Suggestions in Gorgias Sidebar

## Current Situation

✅ **Integration is working!** - You can see `200 OK` and `202 ACCEPTED` responses  
✅ **AI is generating responses** - They're being cached in Railway  
❌ **You can't see them** - Because it's a webhook, not a sidebar widget  

## The Problem

Your current "AI Response Suggestion" integration is type **HTTP webhook**:
- It receives data FROM Gorgias ✅
- It processes in background ✅
- But it doesn't DISPLAY anything in Gorgias ❌

## The Solution: Add a Sidebar App

You need to create a **second integration** (Sidebar App) that displays the AI suggestions.

---

## Step-by-Step: Create Gorgias Sidebar App

### Step 1: Go to Gorgias Settings

1. Open Gorgias
2. Click **Settings** (bottom left)
3. Go to **App Store** (or **Integrations**)
4. Click **Create Your Own App** or **Custom Sidebar App**

### Step 2: Configure the Sidebar App

**Basic Settings:**
- **Name:** AI Response Suggestions
- **Description:** Shows AI-generated response suggestions
- **Type:** Sidebar App
- **Context:** Ticket

**Display Settings:**
- **Position:** Right sidebar
- **Width:** 400px (or full width)
- **Height:** Auto

**URL Configuration:**
- **URL:** `https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}`
- **Method:** GET (iframe)

### Step 3: Set Permissions

Allow the app to:
- ✅ Read ticket data
- ✅ Read customer data
- ✅ Access in ticket view

### Step 4: Save and Activate

1. Click **Save**
2. Click **Activate** or **Install**
3. The sidebar should appear in ticket views

---

## Alternative: Use Gorgias App Builder

If the above doesn't work, use the App Builder:

### Step 1: Create New App

```
Settings → Integrations → HTTP Integrations → New Integration
```

**OR**

```
Settings → Apps → Create Custom App
```

### Step 2: Configure as Sidebar Widget

**Type:** Sidebar Widget  
**Name:** AI Suggestions  
**Context:** ticket  

**Widget Configuration:**
```json
{
  "type": "standalone",
  "context": "ticket",
  "template": "<iframe src='https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}' style='width:100%;height:600px;border:none;'></iframe>"
}
```

---

## Quick Alternative: Manual Access

While setting up the sidebar app, you can manually access suggestions:

### For Ticket 190965582:
```
https://blosh-ai-new-production.up.railway.app/widget/190965582
```

Just replace the ticket ID with any ticket you want to see suggestions for.

---

## Expected Result

Once the sidebar app is configured, when you open a ticket:

1. **Gorgias loads ticket view**
2. **Right sidebar shows iframe** with your widget
3. **Widget displays:**
   - "🤖 AI Suggestion"
   - Loading spinner (if generating)
   - AI response (when ready)
   - Quality score badge
   - "Use Response" and "Copy" buttons
   - Feedback buttons

### Screenshot of What You'll See:

```
┌─────────────────────────────────┐
│ 🤖 AI Suggestion                │
│ ────────────────────────────── │
│ [Freebird Icons] [High Quality]│
│                                 │
│ ┌─────────────────────────────┐│
│ │ Hi Anne,                    ││
│ │                             ││
│ │ Bedankt voor je bericht.    ││
│ │ We hebben je huisnummer     ││
│ │ aangepast...                ││
│ │                             ││
│ │ Met vriendelijke groet,     ││
│ │ Team Freebird               ││
│ │ 020 8081004                 ││
│ └─────────────────────────────┘│
│                                 │
│ [✓ Use Response]  [📋 Copy]    │
│                                 │
│ Was this helpful?               │
│ [👍 Used It] [✏️ Edited] [👎]  │
└─────────────────────────────────┘
```

---

## Temporary Solution (While Setting Up Sidebar)

### Option 1: Check Railway Logs

After opening a ticket, check Railway logs:
```
Background: Generated and cached suggestion for 190965582 - Quality: 85
```

The full response is logged there.

### Option 2: Open Widget in New Tab

When you open ticket 190965582, open in new tab:
```
https://blosh-ai-new-production.up.railway.app/widget/190965582
```

Copy the suggestion from there.

### Option 3: Use API Directly

```bash
curl https://blosh-ai-new-production.up.railway.app/api/suggest/190965582
```

---

## Why Some Tickets Show 200 OK vs 202 ACCEPTED

- **202 ACCEPTED** = New ticket, generating suggestion in background
- **200 OK** = Cached suggestion, returned immediately

Both are successful! The difference is:
- First request: Returns 202, processes in background
- Subsequent requests: Returns 200 with cached result

---

## Next Steps

1. **Wait for Railway deployment** to finish (1-2 minutes)
2. **Create Gorgias Sidebar App** (follow steps above)
3. **Test by opening a ticket** - You should see the AI widget!

Would you like me to help you create the Gorgias Sidebar App configuration?

