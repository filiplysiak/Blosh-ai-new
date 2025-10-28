# Run Gorgias Widget Locally (No Railway Needed)

## Step 1: Install ngrok (1 min)

Download from: https://ngrok.com/download

Or install with:
```bash
winget install ngrok
```

## Step 2: Start the Server (30 seconds)

```bash
cd C:\GitHub\Blosh_fresh\Blosh-ai\gorgias_widget
python widget_server.py
```

Server starts on `http://localhost:5000`

## Step 3: Expose with ngrok (30 seconds)

**Open a NEW terminal:**
```bash
ngrok http 5000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

**Copy that URL!** (e.g., `https://abc123.ngrok.io`)

## Step 4: Create the Widget (1 min)

1. **Edit `create_widget.py` line 12:**
```python
YOUR_API_URL = "https://abc123.ngrok.io"  # Your ngrok URL
```

2. **Run:**
```bash
python create_widget.py
```

## Done!

Widget is now in your Gorgias sidebar! Open any ticket to see AI suggestions.

---

## Keep It Running

While your PC is on and ngrok is running, the widget works!

**To stop:** Close both terminal windows (server + ngrok)

**To restart:** Run steps 2 & 3 again (ngrok URL might change)

