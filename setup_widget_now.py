#!/usr/bin/env python3
"""
Quick Gorgias Widget Setup
Run this locally to set up the AI widget in Gorgias.
"""

import requests
import getpass

# Configuration
GORGIAS_BASE_URL = "https://freebirdicons.gorgias.com/api"
RAILWAY_URL = "https://blosh-ai-new-production.up.railway.app"

def main():
    print("=" * 60)
    print("Quick Gorgias AI Widget Setup")
    print("=" * 60)

    # Get credentials
    email = input("Enter your Gorgias email: ").strip()
    api_key = getpass.getpass("Enter your Gorgias API key: ").strip()

    if not email or not api_key:
        print("ERROR: Email and API key are required")
        return

    # Create Basic auth
    import base64
    auth_string = f"{email}:{api_key}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    auth_header = f"Basic {auth_b64}"

    print(f"Using email: {email}")
    print(f"Auth header created: {auth_header[:20]}...")

    # Widget configuration
    widget_data = {
        "name": "AI Response Suggestion",
        "description": "AI-powered response suggestions for customer support tickets",
        "type": "custom_html",
        "position": "right_sidebar",
        "settings": {
            "html": f'''<iframe
  src="{RAILWAY_URL}/widget/{{{{ticket.id}}}}"
  width="100%"
  height="700px"
  frameborder="0"
  style="border: none; min-height: 700px;"
></iframe>'''
        },
        "display_conditions": [
            {
                "type": "ticket_status",
                "operator": "is_not",
                "value": "closed"
            }
        ],
        "enabled": True
    }

    # Make request to Gorgias API
    url = f"{GORGIAS_BASE_URL}/widgets"
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("\nCreating widget...")
    try:
        response = requests.post(url, headers=headers, json=widget_data)

        if response.status_code == 201:
            result = response.json()
            print("=" * 60)
            print("SUCCESS! AI Widget created in Gorgias")
            print("=" * 60)
            print(f"Widget ID: {result.get('id')}")
            print(f"Widget Name: {result.get('name')}")
            print(f"Position: Right sidebar")
            print(f"URL: {RAILWAY_URL}/widget/{{ticket.id}}")
            print("\nThe widget will now appear in Gorgias for open tickets!")
            print("Refresh any open tickets to see the AI suggestions.")
        else:
            print(f"ERROR: Failed to create widget (HTTP {response.status_code})")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
