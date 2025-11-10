"""
Test script to verify API handles both list and dict formats
"""
import requests
import json

# Test with local server (change URL for Railway)
BASE_URL = "http://localhost:5000"  # Change to Railway URL when testing production

def test_dict_format():
    """Test with dictionary format"""
    print("\n" + "="*60)
    print("TEST 1: Dictionary Format")
    print("="*60)
    
    data = {
        "ticket_id": "123456",
        "customer_name": "Test User",
        "message": "Ik wil graag retour doen",
        "subject": "Retour"
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/suggest",
            json=data,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ DICT FORMAT: PASSED")
            return True
        else:
            print("❌ DICT FORMAT: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_list_format():
    """Test with list format (Gorgias style)"""
    print("\n" + "="*60)
    print("TEST 2: List Format (Gorgias)")
    print("="*60)
    
    data = [{
        "ticket_id": "123456",
        "customer_name": "Test User",
        "message": "Ik wil graag retour doen",
        "subject": "Retour"
    }]
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/suggest",
            json=data,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ LIST FORMAT: PASSED")
            return True
        else:
            print("❌ LIST FORMAT: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_invalid_format():
    """Test with invalid format"""
    print("\n" + "="*60)
    print("TEST 3: Invalid Format (should fail gracefully)")
    print("="*60)
    
    data = "invalid string data"
    
    print(f"Sending: {data}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/suggest",
            json=data,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ INVALID FORMAT: Handled correctly (400 error)")
            return True
        else:
            print("❌ INVALID FORMAT: Should return 400")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST 0: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ HEALTH CHECK: PASSED")
            return True
        else:
            print("❌ HEALTH CHECK: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\n⚠️  Make sure the server is running!")
        print("   Run: python API_widget_server.py")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 GORGIAS API FORMAT TESTS")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    print("\nNote: Set OPENAI_API_KEY environment variable for full test")
    
    results = []
    
    # Test health first
    if not test_health():
        print("\n❌ Server not responding. Aborting tests.")
        return
    
    # Run format tests
    results.append(("Dict Format", test_dict_format()))
    results.append(("List Format", test_list_format()))
    results.append(("Invalid Format", test_invalid_format()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")

if __name__ == "__main__":
    # For Railway testing, uncomment and update:
    # BASE_URL = "https://your-railway-app.railway.app"
    
    main()

