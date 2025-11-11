"""
Suggestion Manager with Rate Limiting and Queuing
Manages AI suggestion generation with OpenAI rate limits
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from queue import Queue, Empty
import os

from database import get_db
from improved_response_generator import generate_response

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for OpenAI API calls
    Implements token bucket algorithm
    """

    def __init__(self, requests_per_minute: int = 10, burst_size: int = 3):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0
        
        logger.info(f"Rate limiter initialized: {requests_per_minute} req/min, burst: {burst_size}")

    def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire a token to make a request
        
        Args:
            timeout: Maximum time to wait for a token (seconds)
            
        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                # Refill tokens based on time passed
                now = time.time()
                time_passed = now - self.last_refill
                tokens_to_add = time_passed * self.refill_rate
                
                if tokens_to_add > 0:
                    self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
                    self.last_refill = now
                
                # Check if we have a token available
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
            
            # Check timeout
            if time.time() - start_time >= timeout:
                logger.warning("Rate limiter timeout - no tokens available")
                return False
            
            # Wait a bit before trying again
            time.sleep(0.1)

    def get_wait_time(self) -> float:
        """Get estimated wait time until next token is available"""
        with self.lock:
            if self.tokens >= 1.0:
                return 0.0
            tokens_needed = 1.0 - self.tokens
            return tokens_needed / self.refill_rate


class SuggestionManager:
    """
    Manages suggestion generation with queuing and rate limiting
    """

    def __init__(self):
        self.db = get_db()
        
        # Rate limiter: 10 requests per minute (conservative for OpenAI)
        self.rate_limiter = RateLimiter(requests_per_minute=10, burst_size=3)
        
        # Background worker
        self.worker_thread = None
        self.worker_running = False
        self.worker_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "generated": 0,
            "failed": 0,
            "queued": 0,
            "rate_limited": 0
        }
        self.stats_lock = threading.Lock()
        
        logger.info("Suggestion manager initialized")

    def start_worker(self):
        """Start the background worker thread"""
        with self.worker_lock:
            if self.worker_running:
                logger.info("Worker already running")
                return
            
            self.worker_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Background worker started")

    def stop_worker(self):
        """Stop the background worker thread"""
        with self.worker_lock:
            if not self.worker_running:
                return
            
            self.worker_running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=5.0)
            logger.info("Background worker stopped")

    def _worker_loop(self):
        """Background worker that processes the queue"""
        logger.info("Worker loop started")
        
        while self.worker_running:
            try:
                # Get next ticket from queue
                ticket_id = self.db.get_next_queued_ticket()
                
                if not ticket_id:
                    # No tickets in queue, wait a bit
                    time.sleep(2.0)
                    continue
                
                # Check if suggestion already exists
                if self.db.has_suggestion(ticket_id):
                    logger.info(f"Suggestion already exists for {ticket_id}, skipping")
                    self.db.update_queue_status(ticket_id, "completed")
                    continue
                
                # Wait for rate limiter
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    logger.info(f"Rate limited, waiting {wait_time:.1f}s before processing {ticket_id}")
                    with self.stats_lock:
                        self.stats["rate_limited"] += 1
                    time.sleep(wait_time)
                
                # Acquire rate limit token
                if not self.rate_limiter.acquire(timeout=30.0):
                    logger.warning(f"Failed to acquire rate limit token for {ticket_id}")
                    time.sleep(5.0)
                    continue
                
                # Generate suggestion
                logger.info(f"Processing ticket {ticket_id}")
                self.db.update_queue_status(ticket_id, "processing")
                
                success = self._generate_for_ticket(ticket_id)
                
                if success:
                    self.db.update_queue_status(ticket_id, "completed")
                    with self.stats_lock:
                        self.stats["generated"] += 1
                    logger.info(f"✅ Successfully generated suggestion for {ticket_id}")
                else:
                    self.db.update_queue_status(ticket_id, "failed", "Generation failed")
                    with self.stats_lock:
                        self.stats["failed"] += 1
                    logger.error(f"❌ Failed to generate suggestion for {ticket_id}")
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(5.0)
        
        logger.info("Worker loop ended")

    def _generate_for_ticket(self, ticket_id: str) -> bool:
        """
        Generate suggestion for a specific ticket
        
        Args:
            ticket_id: Ticket ID to generate for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get ticket data
            ticket = self.db.get_ticket(ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found in database")
                return False
            
            # Check if we have a customer message
            message = ticket.get("last_customer_message")
            if not message or len(message.strip()) < 10:
                logger.warning(f"Ticket {ticket_id} has no valid customer message")
                return False
            
            # Generate response using improved_response_generator
            result = generate_response(
                customer_message=message,
                customer_name=ticket.get("customer_name", ""),
                order_number=ticket.get("order_number"),
                email=ticket.get("customer_email"),
                subject=ticket.get("subject")
            )
            
            if not result:
                logger.error(f"generate_response returned None for {ticket_id}")
                return False
            
            # Store suggestion in database
            suggestion = {
                "ticket_id": ticket_id,
                "suggestion_text": result["response"],
                "quality_score": result.get("quality_score", 0),
                "confidence": result.get("quality_score", 0),
                "brand": result.get("brand", "Unknown"),
                "warnings": result.get("warnings", []),
                "approved": result.get("approved", False),
                "model_id": "ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            success = self.db.upsert_suggestion(suggestion)
            
            if success:
                logger.info(f"Stored suggestion for {ticket_id} (quality: {result['quality_score']}%)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating suggestion for {ticket_id}: {e}", exc_info=True)
            return False

    def generate_suggestion_async(self, ticket_id: str, priority: int = 0) -> bool:
        """
        Queue a ticket for suggestion generation
        
        Args:
            ticket_id: Ticket ID to generate for
            priority: Priority (higher = processed first)
            
        Returns:
            True if queued successfully
        """
        try:
            # Check if already has suggestion
            if self.db.has_suggestion(ticket_id):
                logger.info(f"Ticket {ticket_id} already has suggestion")
                return True
            
            # Add to queue
            success = self.db.queue_generation(ticket_id, priority)
            
            if success:
                with self.stats_lock:
                    self.stats["queued"] += 1
                logger.info(f"Queued ticket {ticket_id} for generation (priority: {priority})")
                
                # Ensure worker is running
                self.start_worker()
            
            return success
            
        except Exception as e:
            logger.error(f"Error queuing ticket {ticket_id}: {e}")
            return False

    def generate_suggestion_sync(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate suggestion synchronously (waits for rate limiter)
        
        Args:
            ticket_id: Ticket ID to generate for
            
        Returns:
            Suggestion dict if successful, None otherwise
        """
        try:
            # Check if already exists
            existing = self.db.get_suggestion(ticket_id)
            if existing:
                return existing
            
            # Wait for rate limiter
            if not self.rate_limiter.acquire(timeout=30.0):
                logger.error(f"Rate limiter timeout for {ticket_id}")
                return None
            
            # Generate
            success = self._generate_for_ticket(ticket_id)
            
            if success:
                return self.db.get_suggestion(ticket_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in sync generation for {ticket_id}: {e}")
            return None

    def ensure_suggestions_for_top_n(self, n: int = 10) -> Dict[str, int]:
        """
        Ensure the top N most recent tickets have suggestions
        
        Args:
            n: Number of recent tickets to ensure suggestions for
            
        Returns:
            Summary dict with counts
        """
        try:
            logger.info(f"Ensuring suggestions for top {n} tickets")
            
            # Get recent tickets
            recent_tickets = self.db.get_recent_tickets(limit=n)
            
            queued = 0
            existing = 0
            skipped = 0
            
            for ticket in recent_tickets:
                ticket_id = ticket["ticket_id"]
                
                # Check if already has suggestion
                if self.db.has_suggestion(ticket_id):
                    existing += 1
                    continue
                
                # Check if has valid message
                message = ticket.get("last_customer_message", "")
                if not message or len(message.strip()) < 10:
                    skipped += 1
                    continue
                
                # Queue for generation (high priority)
                if self.generate_suggestion_async(ticket_id, priority=10):
                    queued += 1
            
            summary = {
                "total": len(recent_tickets),
                "existing": existing,
                "queued": queued,
                "skipped": skipped
            }
            
            logger.info(f"Top {n} tickets summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error ensuring suggestions for top {n}: {e}")
            return {"error": str(e)}

    def get_top_n_tickets(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N most recent tickets"""
        return self.db.get_recent_tickets(limit=n)

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        with self.stats_lock:
            stats = self.stats.copy()
        
        stats["worker_running"] = self.worker_running
        stats["queue"] = self.db.get_queue_stats()
        stats["rate_limiter"] = {
            "tokens_available": self.rate_limiter.tokens,
            "wait_time_seconds": self.rate_limiter.get_wait_time()
        }
        
        return stats


# Singleton instance
_manager_instance = None


def get_manager() -> SuggestionManager:
    """Get or create suggestion manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SuggestionManager()
        logger.info("Suggestion manager instance created")
    return _manager_instance

