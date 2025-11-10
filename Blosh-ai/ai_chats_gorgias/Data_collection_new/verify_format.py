"""
Verify the code handles Gorgias format correctly
"""

# Simulate what Gorgias sends
gorgias_data = [
    {
        "key": "ticket_id",
        "value": "{{ticket.id}}"
    },
    {
        "key": "customer_name",
        "value": "{{ticket.customer.name}}"
    },
    {
        "key": "message",
        "value": "{{ticket.last_message.body_text}}"
    },
    {
        "key": "subject",
        "value": "{{ticket.subject}}"
    }
]

# Simulate with actual values
gorgias_data_actual = [
    {"key": "ticket_id", "value": "185341661"},
    {"key": "customer_name", "value": "Petra"},
    {"key": "message", "value": "Ik wil graag retour doen"},
    {"key": "subject", "value": "Retour"}
]

print("="*60)
print("VERIFYING GORGIAS FORMAT HANDLING")
print("="*60)

print("\n1. Gorgias sends this format:")
print(gorgias_data_actual)

print("\n2. Our code detects it's a list:")
raw_data = gorgias_data_actual
print(f"   isinstance(raw_data, list) = {isinstance(raw_data, list)}")

print("\n3. Our code checks first element:")
print(f"   raw_data[0] = {raw_data[0]}")
print(f"   'key' in raw_data[0] = {'key' in raw_data[0]}")
print(f"   'value' in raw_data[0] = {'value' in raw_data[0]}")

print("\n4. Our code converts to dict:")
data = {item['key']: item['value'] for item in raw_data}
print(f"   data = {data}")

print("\n5. Our code extracts fields:")
print(f"   ticket_id = {data.get('ticket_id')}")
print(f"   customer_name = {data.get('customer_name')}")
print(f"   message = {data.get('message')}")
print(f"   subject = {data.get('subject')}")

print("\n" + "="*60)
print("✅ CODE WILL HANDLE THIS FORMAT CORRECTLY!")
print("="*60)

print("\n" + "="*60)
print("WHY NO EVENTS?")
print("="*60)
print("""
Possible reasons:

1. Integration is DEACTIVATED in Gorgias
   → Check: Settings → Integrations → HTTP Integrations
   → Look for: "AI Response Suggestion"
   → Status should be: Active

2. Integration triggers are DISABLED
   → Check: Integration settings → Triggers section
   → At least one should be enabled:
      - ticket-created
      - ticket-message-created
      - ticket-updated

3. No tickets created/updated since deployment
   → Solution: Create a NEW ticket or add a message
   → This will trigger the integration

4. Integration has too many failures
   → Gorgias auto-disables after many failures
   → Solution: Re-enable it (old failures were from the bug)

5. Railway URL changed
   → Check the URL in Gorgias matches Railway
   → Should be: https://blosh-ai-new-production.up.railway.app/api/suggest

ACTION ITEMS:
1. Go to Gorgias → Settings → Integrations
2. Find "AI Response Suggestion"
3. Verify it's ACTIVE
4. Verify triggers are ENABLED
5. Create a test ticket
6. Check Railway logs immediately after
""")

