"""
Cleanup Test Data
Removes test tickets and suggestions from the database
"""

import logging
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_test_data():
    """Remove test data from database"""
    db = get_db()
    
    test_ticket_ids = [
        "test_12345",
        "test_gen_123",
        "test_queue_1"
    ]
    
    logger.info("Cleaning up test data...")
    
    # Delete from suggestions first (foreign key constraint)
    for ticket_id in test_ticket_ids:
        try:
            with db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete suggestion
                cursor.execute("DELETE FROM suggestions WHERE ticket_id = ?", (ticket_id,))
                logger.info(f"Deleted suggestion for {ticket_id}")
                
                # Delete from queue
                cursor.execute("DELETE FROM generation_queue WHERE ticket_id = ?", (ticket_id,))
                logger.info(f"Deleted queue entry for {ticket_id}")
                
                # Delete ticket
                cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
                logger.info(f"Deleted ticket {ticket_id}")
                
        except Exception as e:
            logger.error(f"Error deleting {ticket_id}: {e}")
    
    # Get stats
    stats = db.get_stats()
    logger.info(f"Database stats after cleanup: {stats}")
    logger.info("✅ Cleanup complete!")


if __name__ == "__main__":
    cleanup_test_data()

