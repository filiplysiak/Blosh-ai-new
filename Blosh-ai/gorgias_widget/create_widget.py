"""
Script to create AI Response Suggestion widget in Gorgias via API
"""

import requests
import json

# Gorgias API Configuration
GORGIAS_BASE_URL = "https://freebirdicons.gorgias.com/api"
GORGIAS_AUTH = "Basic Z2luZ2VyQGJsb3NoLmNvbTo0OTVmMWE3OTQzOGVkOTk5YWNjZTg1MGU4ODJlMWZiY2RhMDhlMTcyY2Y0ODBjMjE2YWFiMDRhZmE4ZTUzMzRi"

# Your deployed API URL (replace with your Railway URL after deployment)
YOUR_API_URL = "https://YOUR-APP.railway.app"

def create_widget():
    """Create AI Response Suggestion widget in Gorgias"""
    
    url = f"{GORGIAS_BASE_URL}/widgets"
    
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json"
    }
    
    # Widget configuration
    widget_config = {
        "title": "🤖 AI Response Suggestion",
        "type": "http-integration",
        "position": "ticket-sidebar",
        "http_integration": {
            "url": f"{YOUR_API_URL}/api/widget/{{{{ticket.id}}}}",
            "method": "GET",
            "headers": {}
        },
        "fields": [
            {
                "key": "suggestion",
                "label": "Suggested Response",
                "type": "text",
                "multiline": True
            },
            {
                "key": "quality_score", 
                "label": "Quality Score",
                "type": "text"
            },
            {
                "key": "confidence",
                "label": "Confidence",
                "type": "text"
            },
            {
                "key": "brand",
                "label": "Brand",
                "type": "text"
            }
        ],
        "enabled": True
    }
    
    print("Creating widget in Gorgias...")
    print(f"API URL: {url}")
    
    response = requests.post(url, json=widget_config, headers=headers)
    
    if response.status_code in [200, 201]:
        widget = response.json()
        print("\n✓ Widget created successfully!")
        print(f"Widget ID: {widget.get('id')}")
        print(f"Title: {widget.get('title')}")
        print("\nWidget is now visible in your Gorgias ticket sidebar!")
        return widget
    else:
        print(f"\n✗ Failed to create widget")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def list_widgets():
    """List all existing widgets"""
    
    url = f"{GORGIAS_BASE_URL}/widgets"
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        widgets = response.json()
        print(f"\nExisting widgets ({len(widgets.get('data', []))}):")
        for widget in widgets.get('data', []):
            print(f"  - {widget.get('title')} (ID: {widget.get('id')})")
        return widgets
    else:
        print(f"Failed to list widgets: {response.status_code}")
        return None

def delete_widget(widget_id):
    """Delete a widget by ID"""
    
    url = f"{GORGIAS_BASE_URL}/widgets/{widget_id}"
    headers = {
        "authorization": GORGIAS_AUTH
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print(f"✓ Widget {widget_id} deleted")
        return True
    else:
        print(f"✗ Failed to delete widget {widget_id}: {response.status_code}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Gorgias AI Widget Creator")
    print("="*60)
    
    # First, update YOUR_API_URL above with your Railway deployment URL!
    if "YOUR-APP" in YOUR_API_URL:
        print("\n⚠️  WARNING: Update YOUR_API_URL in this script first!")
        print("   Deploy the server, then set YOUR_API_URL to your Railway URL")
        print("\n   Example: YOUR_API_URL = 'https://blosh-ai.railway.app'")
        exit(1)
    
    # List existing widgets first
    print("\nStep 1: Checking existing widgets...")
    list_widgets()
    
    # Create the widget
    print("\nStep 2: Creating AI Response Suggestion widget...")
    widget = create_widget()
    
    if widget:
        print("\n" + "="*60)
        print("SUCCESS! Widget is now in your Gorgias sidebar")
        print("="*60)
        print("\nNext steps:")
        print("1. Open any ticket in Gorgias")
        print("2. Look at the right sidebar")
        print("3. You should see '🤖 AI Response Suggestion'")
        print("4. AI suggestions will appear automatically!")

