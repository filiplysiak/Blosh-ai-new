"""
Update existing Gorgias HTTP Integration to use correct endpoint
"""

import os
import requests

# Configuration
GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
RAILWAY_URL = "https://blosh-ai-new-production.up.railway.app"

# The integration ID from your Gorgias (visible in the HTML you sent)
INTEGRATION_ID = 140986  # "AI Response Suggestion" integration

def update_integration():
    """Update the HTTP integration to use correct endpoint and method"""
    
    if not GORGIAS_AUTH:
        print("Error: GORGIAS_AUTH environment variable not set")
        return False
    
    url = f"{GORGIAS_BASE_URL}/integrations/{INTEGRATION_ID}"
    
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json",
        "accept": "application/json"
    }
    
    # Updated configuration
    update_data = {
        "http": {
            "url": f"{RAILWAY_URL}/api/widget-data/{{{{ticket.id}}}}",
            "method": "GET",  # Changed from POST to GET
            "headers": {},
            "triggers": {
                "ticket-created": True,
                "ticket-message-created": True,
                "ticket-updated": True
            },
            "request_content_type": "application/json",
            "response_content_type": "application/json"
        }
    }
    
    print("="*60)
    print("Updating HTTP Integration")
    print("="*60)
    print(f"Integration ID: {INTEGRATION_ID}")
    print(f"New URL: {RAILWAY_URL}/api/widget-data/{{{{ticket.id}}}}")
    print(f"New Method: GET (was POST)")
    print()
    
    try:
        response = requests.put(url, json=update_data, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            integration = response.json()
            print("SUCCESS! HTTP Integration updated")
            print()
            print(f"Integration ID: {integration.get('id')}")
            print(f"Name: {integration.get('name')}")
            print(f"URL: {integration.get('http', {}).get('url')}")
            print(f"Method: {integration.get('http', {}).get('method')}")
            print()
            print("="*60)
            print("The widget should now work!")
            print("="*60)
            print()
            print("Test it:")
            print("1. Refresh your Gorgias page")
            print("2. Open any recent ticket")
            print("3. Check the right sidebar")
            print("4. The AI suggestion should appear!")
            print()
            return True
        else:
            print(f"Failed to update integration")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Fix Gorgias HTTP Integration")
    print("="*60)
    print()
    print("This will update the integration to:")
    print("- Use GET instead of POST")
    print("- Call /api/widget-data/<ticket_id> endpoint")
    print()
    
    success = update_integration()
    
    if not success:
        print()
        print("Make sure GORGIAS_AUTH is set:")
        print('  $env:GORGIAS_AUTH = "Basic [your_credentials]"')
        print()

