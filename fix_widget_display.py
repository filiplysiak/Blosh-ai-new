"""
Fix widget display conditions to show for all ticket types
"""

import os
import requests

GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
WIDGET_ID = 11294481

def update_widget():
    """Update widget to ensure it displays for all tickets"""
    
    if not GORGIAS_AUTH:
        print("Error: GORGIAS_AUTH not set")
        return False
    
    url = f"{GORGIAS_BASE_URL}/widgets/{WIDGET_ID}"
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json"
    }
    
    # First, get current widget config
    print("Fetching current widget configuration...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch widget: {response.status_code}")
        return False
    
    current_widget = response.json()
    print(f"Current widget context: {current_widget.get('context')}")
    print(f"Current widget type: {current_widget.get('type')}")
    print(f"Current widget order: {current_widget.get('order')}")
    
    # Check if there are any conditions limiting display
    if 'conditions' in current_widget:
        print(f"Current conditions: {current_widget['conditions']}")
    else:
        print("No display conditions set")
    
    # Update to ensure it shows for all tickets
    update_data = {
        "order": 0  # Display first
    }
    
    print("\nUpdating widget to display first...")
    response = requests.put(url, json=update_data, headers=headers)
    
    if response.status_code in [200, 201, 202]:
        print("SUCCESS! Widget updated")
        updated = response.json()
        print(f"Order: {updated.get('order')}")
        return True
    else:
        print(f"Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Fix Widget Display")
    print("="*60)
    print()
    
    success = update_widget()
    
    if success:
        print("\nWidget should now display correctly!")
        print("Refresh Gorgias and open any ticket to test.")
    else:
        print("\nFailed to update widget")
        print("Make sure GORGIAS_AUTH is set")




