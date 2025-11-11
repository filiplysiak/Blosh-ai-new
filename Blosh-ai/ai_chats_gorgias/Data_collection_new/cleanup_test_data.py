"""
Cleanup Test Data
Removes test tickets and suggestions from the database
Run this on Railway or locally to clean up test data
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_test_data():
    """Remove test data from database"""
    db = get_db()
    
    # Test ticket patterns
    test_patterns = [
        "test_%",  # Matches test_12345, test_gen_123, etc.
    ]
    
    logger.info("=" * 60)
    logger.info("Cleaning up test data...")
    logger.info("=" * 60)
    
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Find all test tickets
            cursor.execute("""
                SELECT ticket_id FROM tickets 
                WHERE ticket_id LIKE 'test_%'
            """)
            test_tickets = [row[0] for row in cursor.fetchall()]
            
            if not test_tickets:
                logger.info("✅ No test data found - database is clean!")
                return
            
            logger.info(f"Found {len(test_tickets)} test tickets to remove:")
            for ticket_id in test_tickets:
                logger.info(f"  - {ticket_id}")
            
            # Delete from suggestions first (foreign key constraint)
            cursor.execute("DELETE FROM suggestions WHERE ticket_id LIKE 'test_%'")
            deleted_suggestions = cursor.rowcount
            logger.info(f"✅ Deleted {deleted_suggestions} test suggestions")
            
            # Delete from queue
            cursor.execute("DELETE FROM generation_queue WHERE ticket_id LIKE 'test_%'")
            deleted_queue = cursor.rowcount
            logger.info(f"✅ Deleted {deleted_queue} test queue entries")
            
            # Delete from feedback
            cursor.execute("DELETE FROM feedback WHERE ticket_id LIKE 'test_%'")
            deleted_feedback = cursor.rowcount
            logger.info(f"✅ Deleted {deleted_feedback} test feedback entries")
            
            # Delete tickets
            cursor.execute("DELETE FROM tickets WHERE ticket_id LIKE 'test_%'")
            deleted_tickets = cursor.rowcount
            logger.info(f"✅ Deleted {deleted_tickets} test tickets")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        return
    
    # Get stats after cleanup
    stats = db.get_stats()
    logger.info("=" * 60)
    logger.info(f"Database stats after cleanup:")
    logger.info(f"  Tickets: {stats['tickets']}")
    logger.info(f"  Suggestions: {stats['suggestions']}")
    logger.info(f"  Queue: {stats['queue']}")
    logger.info("=" * 60)
    logger.info("✅ Cleanup complete! All test data removed.")


if __name__ == "__main__":
    cleanup_test_data()

