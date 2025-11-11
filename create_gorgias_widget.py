#!/usr/bin/env python3
"""
Gorgias Widget Creator via API
Automatically creates and configures the AI suggestion widget in Gorgias.
"""

import os
import json
import requests
from typing import Dict, Any, Optional


def get_gorgias_auth() -> Optional[str]:
    """Get Gorgias authentication header."""
    return os.getenv("GORGIAS_AUTH")


def get_gorgias_base_url() -> str:
    """Get Gorgias base URL."""
    return os.getenv("GORGIAS_BASE_URL", "https://freebirdicons.gorgias.com/api")


def make_gorgias_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Make a request to Gorgias API."""
    auth = get_gorgias_auth()
    if not auth:
        print("ERROR: GORGIAS_AUTH environment variable not set")
        return None

    base_url = get_gorgias_base_url()
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    headers = {
        "Authorization": auth,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"ERROR: Unsupported HTTP method: {method}")
            return None

        if response.status_code >= 400:
            print(f"ERROR: Gorgias API error {response.status_code}: {response.text}")
            return None

        if response.content:
            return response.json()
        return {}

    except requests.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return None


def get_existing_widgets() -> Optional[list]:
    """Get list of existing widgets."""
    return make_gorgias_request("GET", "widgets")


def create_html_widget() -> bool:
    """Create the HTML widget for AI suggestions."""

    widget_data = {
        "name": "AI Response Suggestion",
        "description": "AI-powered response suggestions for customer support tickets",
        "type": "custom_html",
        "position": "right_sidebar",
        "settings": {
            "html": '''<iframe
  src="https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}"
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

    print("Creating HTML widget for AI suggestions...")
    result = make_gorgias_request("POST", "widgets", widget_data)

    if result:
        print(f"SUCCESS: Widget created successfully! ID: {result.get('id')}")
        return True
    else:
        print("ERROR: Failed to create widget")
        return False


def update_existing_widget(widget_id: str) -> bool:
    """Update an existing widget."""

    widget_data = {
        "name": "AI Response Suggestion",
        "description": "AI-powered response suggestions for customer support tickets",
        "type": "custom_html",
        "position": "right_sidebar",
        "settings": {
            "html": '''<iframe
  src="https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}"
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

    print(f"Updating existing widget (ID: {widget_id})...")
    result = make_gorgias_request("PUT", f"widgets/{widget_id}", widget_data)

    if result:
        print("SUCCESS: Widget updated successfully!")
        return True
    else:
        print("ERROR: Failed to update widget")
        return False


def find_ai_widget(widgets: list) -> Optional[Dict]:
    """Find existing AI widget."""
    for widget in widgets:
        if "AI" in widget.get("name", "") or "ai" in widget.get("name", "").lower():
            return widget
    return None


def main():
    """Main function to create or update the Gorgias widget."""
    print("=" * 60)
    print("Gorgias AI Widget Setup via API")
    print("=" * 60)

    # Check environment variables
    auth = get_gorgias_auth()
    base_url = get_gorgias_base_url()

    if not auth:
        print("ERROR: GORGIAS_AUTH environment variable not set!")
        print("   Please set it with: export GORGIAS_AUTH='Basic [your_base64_auth]'")
        return False

    print(f"SUCCESS: Gorgias URL: {base_url}")
    print(f"SUCCESS: Authentication: {'Set' if auth else 'Missing'}")

    # Get existing widgets
    print("\nChecking existing widgets...")
    widgets = get_existing_widgets()

    if widgets is None:
        print("ERROR: Failed to fetch existing widgets")
        return False

    print(f"Found {len(widgets)} existing widgets")

    # Check if AI widget already exists
    existing_ai_widget = find_ai_widget(widgets)

    if existing_ai_widget:
        print(f"Found existing AI widget: '{existing_ai_widget['name']}' (ID: {existing_ai_widget['id']})")
        print("Updating existing widget...")
        success = update_existing_widget(existing_ai_widget['id'])
    else:
        print("No AI widget found, creating new one...")
        success = create_html_widget()

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS! AI Widget configured in Gorgias")
        print("=" * 60)
        print("Widget will appear in the right sidebar for open tickets")
        print("URL: https://blosh-ai-new-production.up.railway.app/widget/{{ticket.id}}")
        print("Displays AI-generated response suggestions")
        print("Works for email tickets and customer inquiries")
        print("=" * 60)
        return True
    else:
        print("\nERROR: Failed to configure widget")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)