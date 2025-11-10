# Gorgias HTTP Integration Format

## How Gorgias Sends Data

When you configure an HTTP integration in Gorgias with a **form** field, Gorgias sends the data as an **array of key-value objects**, not as a simple JSON dictionary.

### Configuration in Gorgias

```json
{
  "http": {
    "method": "POST",
    "url": "https://blosh-ai-new-production.up.railway.app/api/suggest",
    "request_content_type": "application/json",
    "form": [
      {"key": "ticket_id", "value": "{{ticket.id}}"},
      {"key": "customer_name", "value": "{{ticket.customer.name}}"},
      {"key": "message", "value": "{{ticket.last_message.body_text}}"},
      {"key": "subject", "value": "{{ticket.subject}}"}
    ]
  }
}
```

### What Gets Sent

**Actual HTTP Request Body:**
```json
[
  {"key": "ticket_id", "value": "185341661"},
  {"key": "customer_name", "value": "Petra"},
  {"key": "message", "value": "Ik wil graag retour doen"},
  {"key": "subject", "value": "Retour"}
]
```

**NOT this (what you might expect):**
```json
{
  "ticket_id": "185341661",
  "customer_name": "Petra",
  "message": "Ik wil graag retour doen",
  "subject": "Retour"
}
```

## Why This Format?

Gorgias uses this format because:
1. It allows dynamic field mapping in their UI
2. It preserves the order of fields
3. It's consistent with their internal form handling

## How We Handle It

Our API now automatically detects and converts this format:

```python
if isinstance(raw_data, list) and 'key' in raw_data[0]:
    # Convert: [{"key": "x", "value": "y"}] → {"x": "y"}
    data = {item['key']: item['value'] for item in raw_data}
```

## Available Variables in Gorgias

You can use these Gorgias template variables in the form configuration:

### Ticket Variables
- `{{ticket.id}}` - Ticket ID
- `{{ticket.subject}}` - Ticket subject
- `{{ticket.status}}` - open/closed
- `{{ticket.channel}}` - email/chat/facebook/etc
- `{{ticket.created_datetime}}` - When ticket was created
- `{{ticket.last_message.body_text}}` - Last message text
- `{{ticket.last_message.body_html}}` - Last message HTML

### Customer Variables
- `{{ticket.customer.id}}` - Customer ID
- `{{ticket.customer.name}}` - Full name
- `{{ticket.customer.firstname}}` - First name
- `{{ticket.customer.lastname}}` - Last name
- `{{ticket.customer.email}}` - Email address

### Order Variables (if Shopify connected)
- `{{ticket.customer.integrations.shopify.last_order.id}}` - Order ID
- `{{ticket.customer.integrations.shopify.last_order.total_price}}` - Order total
- `{{ticket.customer.integrations.shopify.customer.orders_count}}` - Number of orders

### Agent Variables
- `{{ticket.assignee_user.name}}` - Assigned agent name
- `{{ticket.assignee_user.email}}` - Assigned agent email
- `{{current_user.name}}` - Current user name

## Current Integration Configuration

**Integration ID:** 140491  
**Name:** AI Response Suggestion  
**URL:** https://blosh-ai-new-production.up.railway.app/api/suggest  
**Method:** POST  
**Content-Type:** application/json

**Form Fields:**
1. `ticket_id` → `{{ticket.id}}`
2. `customer_name` → `{{ticket.customer.name}}`
3. `message` → `{{ticket.last_message.body_text}}`
4. `subject` → `{{ticket.subject}}`

**Triggers:**
- ✅ ticket-created
- ✅ ticket-message-created  
- ✅ ticket-updated

## Testing the Integration

### Test with curl (Gorgias format):
```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/suggest \
  -H "Content-Type: application/json" \
  -d '[
    {"key": "ticket_id", "value": "123456"},
    {"key": "customer_name", "value": "Test User"},
    {"key": "message", "value": "Ik wil graag retour doen"},
    {"key": "subject", "value": "Retour"}
  ]'
```

### Test with curl (Simple dict format):
```bash
curl -X POST https://blosh-ai-new-production.up.railway.app/api/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "123456",
    "customer_name": "Test User",
    "message": "Ik wil graag retour doen",
    "subject": "Retour"
  }'
```

Both formats now work! ✅

## Expected Railway Logs

When Gorgias triggers the integration, you should see:

```
INFO:API_widget_server:Received raw data type: <class 'list'>
INFO:API_widget_server:Received raw data: [{'key': 'ticket_id', 'value': '185341661'}, ...]
INFO:API_widget_server:Converted Gorgias form array to dict: {'ticket_id': '185341661', 'customer_name': 'Petra', ...}
INFO:API_widget_server:Generating suggestion for ticket 185341661
INFO:API_widget_server:Generated suggestion for 185341661 - Quality: 85
```

## Troubleshooting

### Still getting errors?
1. Check Railway logs for the ACTUAL data format received
2. The logs will show: `Received raw data: [...]`
3. Verify the Gorgias integration configuration matches the format above

### Gorgias Integration Not Triggering?
1. Check integration is **active** (not deactivated)
2. Verify triggers are enabled (ticket-created, ticket-message-created, ticket-updated)
3. Test by creating a new ticket or adding a message to existing ticket
4. Check Gorgias integration logs for errors

### Widget Not Showing?
The current integration is a **webhook** (HTTP POST), not a **widget**.
- It sends data TO your API
- It doesn't display anything in Gorgias UI
- To show AI suggestions in Gorgias, you need a separate **Sidebar App** integration

---
**Last Updated:** November 10, 2025  
**Status:** ✅ Fixed and deployed

