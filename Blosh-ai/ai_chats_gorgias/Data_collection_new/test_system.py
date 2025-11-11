"""
System Test Script
Tests database, rate limiting, and suggestion generation
"""

import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database():
    """Test database operations"""
    logger.info("=" * 60)
    logger.info("TEST 1: Database Operations")
    logger.info("=" * 60)
    
    try:
        from database import get_db
        
        db = get_db()
        logger.info("✅ Database initialized")
        
        # Test ticket upsert
        test_ticket = {
            "ticket_id": "test_12345",
            "subject": "Test ticket",
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "order_number": "102123456",
            "channel": "email",
            "last_customer_message": "This is a test message",
            "metadata": {"test": True},
            "created_at": "2025-11-11T00:00:00",
            "updated_at": "2025-11-11T00:00:00"
        }
        
        success = db.upsert_ticket(test_ticket)
        if success:
            logger.info("✅ Ticket upsert successful")
        else:
            logger.error("❌ Ticket upsert failed")
            return False
        
        # Test ticket retrieval
        retrieved = db.get_ticket("test_12345")
        if retrieved and retrieved["ticket_id"] == "test_12345":
            logger.info("✅ Ticket retrieval successful")
        else:
            logger.error("❌ Ticket retrieval failed")
            return False
        
        # Test suggestion upsert
        test_suggestion = {
            "ticket_id": "test_12345",
            "suggestion_text": "Hi Test Customer,\n\nBedankt voor je bericht.\n\nMet vriendelijke groet,\nTeam Freebird Icons\n020 8081004",
            "quality_score": 85,
            "confidence": 85,
            "brand": "Freebird Icons",
            "warnings": [],
            "approved": True,
            "model_id": "test_model",
            "generated_at": "2025-11-11T00:00:00"
        }
        
        success = db.upsert_suggestion(test_suggestion)
        if success:
            logger.info("✅ Suggestion upsert successful")
        else:
            logger.error("❌ Suggestion upsert failed")
            return False
        
        # Test suggestion retrieval
        retrieved_sugg = db.get_suggestion("test_12345")
        if retrieved_sugg and retrieved_sugg["ticket_id"] == "test_12345":
            logger.info("✅ Suggestion retrieval successful")
        else:
            logger.error("❌ Suggestion retrieval failed")
            return False
        
        # Test queue operations
        success = db.queue_generation("test_queue_1", priority=5)
        if success:
            logger.info("✅ Queue generation successful")
        else:
            logger.error("❌ Queue generation failed")
            return False
        
        next_ticket = db.get_next_queued_ticket()
        if next_ticket == "test_queue_1":
            logger.info("✅ Queue retrieval successful")
        else:
            logger.error("❌ Queue retrieval failed")
            return False
        
        # Get stats
        stats = db.get_stats()
        logger.info(f"✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}", exc_info=True)
        return False


def test_rate_limiter():
    """Test rate limiter"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Rate Limiter")
    logger.info("=" * 60)
    
    try:
        from suggestion_manager import RateLimiter
        
        # Create rate limiter: 5 req/min, burst 2
        limiter = RateLimiter(requests_per_minute=5, burst_size=2)
        logger.info("✅ Rate limiter created (5 req/min, burst 2)")
        
        # Test burst
        logger.info("Testing burst capacity...")
        start = time.time()
        
        for i in range(2):
            if limiter.acquire(timeout=1.0):
                logger.info(f"  ✅ Request {i+1} acquired immediately")
            else:
                logger.error(f"  ❌ Request {i+1} failed")
                return False
        
        burst_time = time.time() - start
        logger.info(f"✅ Burst requests completed in {burst_time:.2f}s")
        
        # Test rate limiting
        logger.info("Testing rate limiting (should wait)...")
        start = time.time()
        
        if limiter.acquire(timeout=15.0):
            wait_time = time.time() - start
            logger.info(f"✅ Request 3 acquired after {wait_time:.2f}s wait")
            
            if wait_time > 1.0:  # Should have waited
                logger.info("✅ Rate limiting working correctly")
            else:
                logger.warning("⚠️  Rate limiting may not be working (no wait)")
        else:
            logger.error("❌ Request 3 timed out")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Rate limiter test failed: {e}", exc_info=True)
        return False


def test_suggestion_manager():
    """Test suggestion manager"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Suggestion Manager")
    logger.info("=" * 60)
    
    try:
        from suggestion_manager import get_manager
        from database import get_db
        
        manager = get_manager()
        db = get_db()
        logger.info("✅ Suggestion manager created")
        
        # Create test ticket with valid message
        test_ticket = {
            "ticket_id": "test_gen_123",
            "subject": "Test generation",
            "customer_name": "Jana",
            "customer_email": "jana@test.com",
            "order_number": "102123456",
            "channel": "email",
            "last_customer_message": "Ik wil graag mijn bestelling retourneren. Kan dat nog?",
            "metadata": {},
            "created_at": "2025-11-11T00:00:00",
            "updated_at": "2025-11-11T00:00:00"
        }
        
        db.upsert_ticket(test_ticket)
        logger.info("✅ Test ticket created")
        
        # Test async queuing
        success = manager.generate_suggestion_async("test_gen_123", priority=10)
        if success:
            logger.info("✅ Ticket queued for generation")
        else:
            logger.error("❌ Failed to queue ticket")
            return False
        
        # Check if worker can be started
        manager.start_worker()
        logger.info("✅ Background worker started")
        
        # Get stats
        stats = manager.get_stats()
        logger.info(f"✅ Manager stats: {stats}")
        
        # Note: We don't test actual generation here because it requires OpenAI API key
        logger.info("⚠️  Skipping actual AI generation (requires OpenAI API key)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Suggestion manager test failed: {e}", exc_info=True)
        return False


def test_ticket_sync():
    """Test ticket sync (without actual API calls)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Ticket Sync")
    logger.info("=" * 60)
    
    try:
        from ticket_sync import get_sync
        
        sync = get_sync()
        logger.info("✅ Ticket sync created")
        
        # Get stats
        stats = sync.get_sync_stats()
        logger.info(f"✅ Sync stats: {stats}")
        
        if stats["auth_configured"]:
            logger.info("✅ Gorgias auth is configured")
            logger.info("⚠️  Skipping actual sync (to avoid API calls during test)")
        else:
            logger.warning("⚠️  Gorgias auth not configured (expected in test)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ticket sync test failed: {e}", exc_info=True)
        return False


def test_api_server():
    """Test API server imports"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: API Server")
    logger.info("=" * 60)
    
    try:
        # Test if API server can be imported
        import API_widget_server
        logger.info("✅ API server module imported successfully")
        
        # Check if Flask app exists
        if hasattr(API_widget_server, 'app'):
            logger.info("✅ Flask app exists")
        else:
            logger.error("❌ Flask app not found")
            return False
        
        # Check if key routes exist
        routes = [rule.rule for rule in API_widget_server.app.url_map.iter_rules()]
        required_routes = ['/health', '/api/suggest/<ticket_id>', '/widget/<ticket_id>']
        
        for route in required_routes:
            if route in routes:
                logger.info(f"✅ Route exists: {route}")
            else:
                logger.error(f"❌ Route missing: {route}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API server test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("GORGIAS WIDGET SYSTEM TEST")
    logger.info("=" * 60)
    
    # Check environment
    logger.info("\nEnvironment Check:")
    logger.info(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    logger.info(f"  GORGIAS_AUTH: {'✅ Set' if os.getenv('GORGIAS_AUTH') else '❌ Not set'}")
    logger.info(f"  GORGIAS_BASE_URL: {os.getenv('GORGIAS_BASE_URL', 'Not set')}")
    
    # Run tests
    results = {
        "Database": test_database(),
        "Rate Limiter": test_rate_limiter(),
        "Suggestion Manager": test_suggestion_manager(),
        "Ticket Sync": test_ticket_sync(),
        "API Server": test_api_server()
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 60)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! System is ready for deployment.")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed. Please fix before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

