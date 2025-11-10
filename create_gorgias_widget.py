"""
Create AI Response Suggestion Widget in Gorgias
Uses Gorgias Widgets API to create a native sidebar widget
"""

import os
import requests
import json

# Configuration
GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')  # Format: "Basic [base64_encoded]"
RAILWAY_URL = "https://blosh-ai-new-production.up.railway.app"

def create_widget():
    """Create the AI suggestion widget in Gorgias"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH environment variable not set")
        print("\nSet it with:")
        print('  export GORGIAS_AUTH="Basic [your_base64_auth]"')
        return None
    
    url = f"{GORGIAS_BASE_URL}/widgets"
    
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json",
        "accept": "application/json"
    }
    
    # Widget configuration using Gorgias's sidebar widget format
    widget_config = {
        "title": "🤖 AI Response Suggestion",
        "type": "http-integration",
        "position": "ticket-sidebar",
        "enabled": True,
        "http_integration": {
            "url": f"{RAILWAY_URL}/widget/{{{{ticket.id}}}}",
            "method": "GET",
            "headers": {},
            "body": None
        },
        "conditions": [
            {
                "field": "ticket.status",
                "operator": "not_equal",
                "value": "closed"
            }
        ]
    }
    
    print("="*60)
    print("Creating Gorgias Widget")
    print("="*60)
    print(f"Gorgias URL: {GORGIAS_BASE_URL}")
    print(f"Railway URL: {RAILWAY_URL}")
    print(f"Widget URL: {RAILWAY_URL}/widget/{{{{ticket.id}}}}")
    print()
    
    try:
        response = requests.post(url, json=widget_config, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            widget = response.json()
            print("✅ Widget created successfully!")
            print()
            print(f"Widget ID: {widget.get('id')}")
            print(f"Title: {widget.get('title')}")
            print(f"Type: {widget.get('type')}")
            print(f"Position: {widget.get('position')}")
            print(f"Enabled: {widget.get('enabled')}")
            print()
            print("="*60)
            print("✅ SUCCESS! Widget is now in your Gorgias sidebar")
            print("="*60)
            print()
            print("Next steps:")
            print("1. Open any ticket in Gorgias")
            print("2. Look at the right sidebar")
            print("3. You should see '🤖 AI Response Suggestion'")
            print("4. AI suggestions will load automatically!")
            print()
            return widget
        else:
            print(f"❌ Failed to create widget")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    print("Errors:")
                    for error in error_data['errors']:
                        print(f"  - {error}")
            except:
                pass
            
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def list_widgets():
    """List all existing widgets in Gorgias"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH not set")
        return None
    
    url = f"{GORGIAS_BASE_URL}/widgets"
    headers = {
        "authorization": GORGIAS_AUTH,
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            widgets = data.get('data', []) if isinstance(data, dict) else data
            
            print(f"\n📋 Existing widgets ({len(widgets)}):")
            print("-" * 60)
            
            if not widgets:
                print("  No widgets found")
            else:
                for widget in widgets:
                    print(f"  • {widget.get('title')} (ID: {widget.get('id')})")
                    print(f"    Type: {widget.get('type')}, Position: {widget.get('position')}")
                    print(f"    Enabled: {widget.get('enabled')}")
                    print()
            
            return widgets
        else:
            print(f"❌ Failed to list widgets: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def delete_widget(widget_id):
    """Delete a widget by ID"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH not set")
        return False
    
    url = f"{GORGIAS_BASE_URL}/widgets/{widget_id}"
    headers = {
        "authorization": GORGIAS_AUTH
    }
    
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 204]:
            print(f"✅ Widget {widget_id} deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete widget {widget_id}: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False

def test_railway_endpoint():
    """Test if Railway endpoint is accessible"""
    
    print("\n🔍 Testing Railway endpoint...")
    print(f"URL: {RAILWAY_URL}/health")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Railway endpoint is healthy!")
            print(f"   Status: {data.get('status')}")
            print(f"   Initialized: {data.get('initialized')}")
            
            db_stats = data.get('database', {})
            print(f"   Total tickets: {db_stats.get('total_tickets', 0)}")
            print(f"   With suggestions: {db_stats.get('tickets_with_suggestions', 0)}")
            print()
            return True
        else:
            print(f"⚠️  Railway returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Railway endpoint: {str(e)}")
        print("\nMake sure your Railway deployment is running!")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Gorgias AI Widget Setup")
    print("="*60)
    print()
    
    # Step 1: Test Railway endpoint
    if not test_railway_endpoint():
        print("\n⚠️  Warning: Railway endpoint is not responding")
        print("   The widget will be created but may not work until Railway is running")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            exit(0)
    
    # Step 2: List existing widgets
    print("\n" + "="*60)
    print("Step 1: Checking existing widgets...")
    print("="*60)
    existing = list_widgets()
    
    # Check if AI widget already exists
    if existing:
        ai_widgets = [w for w in existing if 'AI' in w.get('title', '')]
        if ai_widgets:
            print("\n⚠️  Found existing AI widget(s):")
            for w in ai_widgets:
                print(f"   • {w.get('title')} (ID: {w.get('id')})")
            
            response = input("\nDelete existing AI widgets first? (y/n): ")
            if response.lower() == 'y':
                for w in ai_widgets:
                    delete_widget(w.get('id'))
                print()
    
    # Step 3: Create the widget
    print("\n" + "="*60)
    print("Step 2: Creating AI Response Suggestion widget...")
    print("="*60)
    print()
    
    widget = create_widget()
    
    if widget:
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        print()
        print("The widget is now installed in your Gorgias account.")
        print()
        print("To use it:")
        print("1. Go to Gorgias and open any ticket")
        print("2. Look at the right sidebar")
        print("3. You'll see '🤖 AI Response Suggestion'")
        print("4. Click 'Generate response' if no suggestion is shown")
        print()
        print("Enjoy your AI-powered customer support! 🚀")
        print()
    else:
        print("\n" + "="*60)
        print("❌ Setup failed")
        print("="*60)
        print()
        print("Please check:")
        print("1. GORGIAS_AUTH environment variable is set correctly")
        print("2. Your Gorgias API credentials are valid")
        print("3. Railway deployment is running")
        print()
        print("For help, see: GORGIAS_WIDGET_SETUP.md")
        print()
