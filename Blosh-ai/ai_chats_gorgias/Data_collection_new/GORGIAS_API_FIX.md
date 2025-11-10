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
Gorgias HTTP integration sends data as a **form array** format:
```json
[
  {"key": "ticket_id", "value": "123456"},
  {"key": "customer_name", "value": "Petra"},
  {"key": "message", "value": "Ik wil retour doen"},
  {"key": "subject", "value": "Retour"}
]
```

But the code expected a simple dictionary:
```json
{
  "ticket_id": "123456",
  "customer_name": "Petra",
  "message": "...",
  "subject": "..."
}
```

This is because Gorgias HTTP integrations use a "form" field with key-value pairs that get sent as an array.

## Solution
Updated both `/api/suggest` and `/api/feedback` endpoints to handle Gorgias form array format:

```python
raw_data = request.get_json()

# Handle Gorgias form array format: [{"key": "ticket_id", "value": "123"}, ...]
if isinstance(raw_data, list):
    if len(raw_data) > 0 and isinstance(raw_data[0], dict):
        if 'key' in raw_data[0] and 'value' in raw_data[0]:
            # Convert Gorgias form array to dict
            data = {item['key']: item['value'] for item in raw_data}
            logger.info(f"Converted Gorgias form array to dict: {data}")
        else:
            # Simple list with one dict element
            data = raw_data[0]
            logger.info("Extracted data from list format")
    else:
        logger.error(f"Unexpected list format: {raw_data}")
        return jsonify({'error': 'Invalid data format'}), 400
elif isinstance(raw_data, dict):
    data = raw_data
    logger.info("Using dict format directly")
else:
    logger.error(f"Unexpected data type: {type(raw_data)}")
    return jsonify({'error': f'Invalid data type: {type(raw_data)}'}), 400
```

The key insight: Gorgias HTTP integrations with "form" fields send data as:
`[{"key": "field_name", "value": "field_value"}, ...]`

We now convert this to a standard dictionary for processing.

## Changes Made
1. ✅ Updated `/api/suggest` endpoint to handle list format
2. ✅ Updated `/api/feedback` endpoint to handle list format
3. ✅ Added logging to track data format for debugging
4. ✅ Added proper error handling for unexpected formats

## Testing
After deploying to Railway, the API should now:
- ✅ Accept Gorgias form array: `[{"key": "ticket_id", "value": "123"}, ...]`
- ✅ Accept simple dict: `{"ticket_id": "123"}`
- ✅ Accept simple list: `[{"ticket_id": "123"}]`
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

