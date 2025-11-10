# Gorgias API Fix - List vs Dict Issue

## Problem
The Gorgias API was sending data as a **list** instead of a **dict**, causing the following error:

```
AttributeError: 'list' object has no attribute 'get'
```

This occurred at line 172 in `API_widget_server.py`:
```python
ticket_id = data.get('ticket_id')
```

## Root Cause
Gorgias can send webhook/API data in two formats:
1. **Dictionary format**: `{"ticket_id": "123", "message": "..."}`
2. **List format**: `[{"ticket_id": "123", "message": "..."}]`

The code was only handling the dictionary format.

## Solution
Updated both `/api/suggest` and `/api/feedback` endpoints to handle both formats:

```python
raw_data = request.get_json()

# Handle both list and dict formats from Gorgias
if isinstance(raw_data, list):
    # Gorgias might send a list with one dict element
    if len(raw_data) > 0 and isinstance(raw_data[0], dict):
        data = raw_data[0]
        logger.info("Extracted data from list format")
    else:
        logger.error(f"Unexpected list format: {raw_data}")
        return jsonify({'error': 'Invalid data format: expected dict or list with dict'}), 400
elif isinstance(raw_data, dict):
    data = raw_data
else:
    logger.error(f"Unexpected data type: {type(raw_data)}")
    return jsonify({'error': f'Invalid data type: {type(raw_data)}'}), 400
```

## Changes Made
1. ✅ Updated `/api/suggest` endpoint to handle list format
2. ✅ Updated `/api/feedback` endpoint to handle list format
3. ✅ Added logging to track data format for debugging
4. ✅ Added proper error handling for unexpected formats

## Testing
After deploying to Railway, the API should now:
- ✅ Accept data as `{"ticket_id": "123"}`
- ✅ Accept data as `[{"ticket_id": "123"}]`
- ✅ Log the received format for debugging
- ✅ Return clear error messages for invalid formats

## Deployment
To deploy the fix to Railway:

1. **Commit the changes:**
   ```bash
   git add Blosh-ai/ai_chats_gorgias/Data_collection_new/API_widget_server.py
   git commit -m "Fix: Handle list format from Gorgias API"
   git push
   ```

2. **Railway will auto-deploy** (if connected to GitHub)

3. **Monitor logs** in Railway dashboard to verify:
   ```
   Received raw data type: <class 'list'>
   Extracted data from list format
   Generating suggestion for ticket 123456
   ```

## Verification
Check Railway logs for:
- ✅ No more `AttributeError: 'list' object has no attribute 'get'`
- ✅ Logs showing "Received raw data type: <class 'list'>"
- ✅ Logs showing "Extracted data from list format"
- ✅ Successful AI response generation

## Date Fixed
November 10, 2025

