"""
Create AI Response Suggestion Widget in Gorgias
Uses Gorgias API to create HTTP integration + widget programmatically
Based on: https://developers.gorgias.com/docs/create-integrations-and-widgets-programmatically
"""

import os
import requests
import json

# Configuration
GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')  # Format: "Basic [base64_encoded]"
RAILWAY_URL = "https://blosh-ai-new-production.up.railway.app"

def create_http_integration():
    """Step 1: Create the HTTP integration that fetches AI suggestions"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH environment variable not set")
        return None
    
    url = f"{GORGIAS_BASE_URL}/integrations"
    
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json",
        "accept": "application/json"
    }
    
    # HTTP integration configuration
    integration_config = {
        "name": "AI Response Suggestion",
        "description": "Fetches AI-generated response suggestions for customer support tickets",
        "type": "http",
        "http": {
            "url": f"{RAILWAY_URL}/api/widget-data/{{{{ticket.id}}}}",
            "method": "GET",
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
    print("Step 1: Creating HTTP Integration")
    print("="*60)
    print(f"Integration URL: {RAILWAY_URL}/api/widget-data/{{{{ticket.id}}}}")
    print()
    
    try:
        response = requests.post(url, json=integration_config, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            integration = response.json()
            integration_id = integration.get('id')
            print(f"✅ HTTP Integration created successfully!")
            print(f"   Integration ID: {integration_id}")
            print(f"   Name: {integration.get('name')}")
            print()
            return integration_id
        else:
            print(f"❌ Failed to create integration")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def create_widget(integration_id):
    """Step 2: Create the widget that displays the integration data"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH environment variable not set")
        return None
    
    if not integration_id:
        print("❌ Error: No integration_id provided")
        return None
    
    url = f"{GORGIAS_BASE_URL}/widgets"
    
    headers = {
        "authorization": GORGIAS_AUTH,
        "content-type": "application/json",
        "accept": "application/json"
    }
    
    # Widget configuration - displays JSON data using Gorgias template
    widget_config = {
        "title": "🤖 AI Response Suggestion",
        "context": "ticket",  # Display in ticket sidebar
        "integration_id": integration_id,
        "template": {
            "type": "wrapper",
            "widgets": [
                # Status field
                {
                    "type": "text",
                    "path": "status",
                    "title": "Status",
                    "order": 0
                },
                # Message field (for generating/no_message states)
                {
                    "type": "text",
                    "path": "message",
                    "title": "",
                    "order": 1,
                    "meta": {
                        "hideIfEmpty": True
                    }
                },
                # Main suggestion text
                {
                    "type": "text",
                    "path": "suggestion_text",
                    "title": "Suggested Response",
                    "order": 2,
                    "meta": {
                        "limit": 2000,
                        "hideIfEmpty": True
                    }
                },
                # Quality score
                {
                    "type": "text",
                    "path": "quality_score",
                    "title": "Quality Score",
                    "order": 3,
                    "meta": {
                        "hideIfEmpty": True
                    }
                },
                # Brand
                {
                    "type": "text",
                    "path": "brand",
                    "title": "Brand",
                    "order": 4,
                    "meta": {
                        "hideIfEmpty": True
                    }
                },
                # Warnings list
                {
                    "type": "list",
                    "path": "warnings",
                    "title": "Warnings",
                    "order": 5,
                    "widgets": [
                        {
                            "type": "text",
                            "path": "",
                            "title": ""
                        }
                    ],
                    "meta": {
                        "hideIfEmpty": True
                    }
                },
                # Timestamp
                {
                    "type": "text",
                    "path": "timestamp",
                    "title": "Generated At",
                    "order": 6,
                    "meta": {
                        "hideIfEmpty": True
                    }
                }
            ],
            "meta": {
                "displayCard": True,
                "custom": {
                    "buttons": [
                        {
                            "label": "🔄 Regenerate",
                            "action": {
                                "url": f"{RAILWAY_URL}/api/suggest",
                                "method": "POST",
                                "body": {
                                    "contentType": "application/json",
                                    "application/json": {
                                        "ticket_id": "{{ticket.id}}"
                                    },
                                    "application/x-www-form-urlencoded": []
                                },
                                "params": [],
                                "headers": []
                            }
                        }
                    ],
                    "links": []
                }
            }
        }
    }
    
    print("="*60)
    print("Step 2: Creating Widget")
    print("="*60)
    print(f"Integration ID: {integration_id}")
    print()
    
    try:
        response = requests.post(url, json=widget_config, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            widget = response.json()
            widget_id = widget.get('id')
            print(f"✅ Widget created successfully!")
            print(f"   Widget ID: {widget_id}")
            print(f"   Title: {widget.get('title')}")
            print()
            print("="*60)
            print("🎉 SETUP COMPLETE!")
            print("="*60)
            print()
            print("The AI Response Suggestion widget is now installed!")
            print()
            print("To use it:")
            print("1. Open any ticket in Gorgias")
            print("2. Look at the right sidebar")
            print("3. You'll see '🤖 AI Response Suggestion'")
            print("4. Click 'Generate response' if needed")
            print()
            return widget
        else:
            print(f"❌ Failed to create widget")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    print("\n   Errors:")
                    for error in error_data['errors']:
                        print(f"   - {error}")
            except:
                pass
            
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def list_integrations():
    """List all existing integrations in Gorgias"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH not set")
        return None
    
    url = f"{GORGIAS_BASE_URL}/integrations"
    headers = {
        "authorization": GORGIAS_AUTH,
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            integrations = data.get('data', []) if isinstance(data, dict) else data
            
            print(f"\n📋 Existing integrations ({len(integrations)}):")
            print("-" * 60)
            
            if not integrations:
                print("  No integrations found")
            else:
                for integration in integrations:
                    print(f"  • {integration.get('name')} (ID: {integration.get('id')})")
                    print(f"    Type: {integration.get('type')}")
                    if integration.get('http'):
                        print(f"    URL: {integration['http'].get('url', 'N/A')}")
                    print()
            
            return integrations
        else:
            print(f"❌ Failed to list integrations: {response.status_code}")
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
                    print(f"    Context: {widget.get('context')}")
                    print(f"    Integration ID: {widget.get('integration_id')}")
                    print()
            
            return widgets
        else:
            print(f"❌ Failed to list widgets: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def delete_integration(integration_id):
    """Delete an integration by ID"""
    
    if not GORGIAS_AUTH:
        print("❌ Error: GORGIAS_AUTH not set")
        return False
    
    url = f"{GORGIAS_BASE_URL}/integrations/{integration_id}"
    headers = {
        "authorization": GORGIAS_AUTH
    }
    
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 204]:
            print(f"✅ Integration {integration_id} deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete integration {integration_id}: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False

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
    print("Gorgias AI Widget Setup (API Method)")
    print("="*60)
    print()
    print("This script creates:")
    print("1. HTTP Integration - fetches AI suggestions from Railway")
    print("2. Widget - displays the suggestions in Gorgias sidebar")
    print()
    print("Based on: https://developers.gorgias.com/docs/create-integrations-and-widgets-programmatically")
    print()
    
    # Step 1: Test Railway endpoint
    if not test_railway_endpoint():
        print("\n⚠️  Warning: Railway endpoint is not responding")
        print("   The integration/widget will be created but may not work until Railway is running")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            exit(0)
    
    # Step 2: List existing integrations and widgets
    print("\n" + "="*60)
    print("Checking existing integrations and widgets...")
    print("="*60)
    existing_integrations = list_integrations()
    existing_widgets = list_widgets()
    
    # Check if AI integration already exists
    if existing_integrations:
        ai_integrations = [i for i in existing_integrations if 'AI' in i.get('name', '')]
        if ai_integrations:
            print("\n⚠️  Found existing AI integration(s):")
            for i in ai_integrations:
                print(f"   • {i.get('name')} (ID: {i.get('id')})")
            
            response = input("\nDelete existing AI integrations first? (y/n): ")
            if response.lower() == 'y':
                for i in ai_integrations:
                    delete_integration(i.get('id'))
                print()
    
    # Check if AI widget already exists
    if existing_widgets:
        ai_widgets = [w for w in existing_widgets if 'AI' in w.get('title', '')]
        if ai_widgets:
            print("\n⚠️  Found existing AI widget(s):")
            for w in ai_widgets:
                print(f"   • {w.get('title')} (ID: {w.get('id')})")
            
            response = input("\nDelete existing AI widgets first? (y/n): ")
            if response.lower() == 'y':
                for w in ai_widgets:
                    delete_widget(w.get('id'))
                print()
    
    # Step 3: Create the HTTP integration
    print("\n" + "="*60)
    print("Creating HTTP Integration and Widget...")
    print("="*60)
    print()
    
    integration_id = create_http_integration()
    
    if not integration_id:
        print("\n❌ Failed to create integration. Cannot proceed.")
        exit(1)
    
    # Step 4: Create the widget
    widget = create_widget(integration_id)
    
    if widget:
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        print()
        print("The AI Response Suggestion widget is now installed!")
        print()
        print("What was created:")
        print(f"  • HTTP Integration (ID: {integration_id})")
        print(f"  • Widget (ID: {widget.get('id')})")
        print()
        print("To use it:")
        print("1. Go to Gorgias and open any ticket")
        print("2. Look at the right sidebar")
        print("3. You'll see '🤖 AI Response Suggestion'")
        print("4. The AI suggestion will load automatically!")
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
        print("4. Integration was created successfully")
        print()
        print("For help, see: GORGIAS_WIDGET_SETUP.md")
        print()
