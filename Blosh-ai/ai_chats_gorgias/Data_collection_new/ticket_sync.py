"""
Ticket Sync Module
Synchronizes tickets from Gorgias API to local database
"""

import logging
import os
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests

from database import get_db

logger = logging.getLogger(__name__)



# WITH THIS:
class TicketSync:
    """Synchronizes tickets from Gorgias API"""

    def __init__(self):
        self.db = get_db()
        # Note: env vars are read via properties to handle Railway timing
        logger.info("Ticket sync instance created")
        
    @property
    def gorgias_auth(self):
        """Get GORGIAS_AUTH fresh each time"""
        return os.getenv("GORGIAS_AUTH")
    
    @property
    def gorgias_base_url(self):
        """Get GORGIAS_BASE_URL fresh each time"""
        return os.getenv("GORGIAS_BASE_URL", "https://freebirdicons.gorgias.com/api")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Gorgias API requests"""
        return {
            "accept": "application/json",
            "authorization": self.gorgias_auth,
            "content-type": "application/json"
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Any]:
        """
        Make a request to Gorgias API with retry logic for rate limits
        
        Args:
            endpoint: API endpoint (e.g., "/tickets")
            params: Query parameters
            max_retries: Maximum number of retries for rate limit errors
            
        Returns:
            Response JSON or None if failed
        """
        if not self.gorgias_auth:
            logger.error("Cannot make request - GORGIAS_AUTH not set")
            return None

        url = f"{self.gorgias_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params or {},
                    timeout=30
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit hit - wait and retry
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    logger.warning(f"Rate limit hit for {endpoint}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Gorgias API error {response.status_code}: {response.text[:200]}")
                    return None

            except requests.RequestException as e:
                logger.error(f"Request failed for {endpoint}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        logger.error(f"Failed to fetch {endpoint} after {max_retries} retries")
        return None

    def _extract_ticket_info(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant information from Gorgias ticket data
        
        Args:
            ticket_data: Raw ticket data from Gorgias API
            
        Returns:
            Cleaned ticket dict for database
        """
        ticket_id = str(ticket_data.get("id", ""))
        
        # Get customer info
        customer = ticket_data.get("customer", {})
        customer_name = ""
        if customer:
            customer_name = customer.get("firstname", "") or customer.get("name", "")
            if customer_name and " " in customer_name:
                customer_name = customer_name.split()[0]
        
        # Get last customer message
        last_customer_message = ""
        messages = ticket_data.get("messages", [])
        
        if messages:
            # Find last message from customer (not agent)
            for msg in reversed(messages):
                if not msg.get("from_agent", True):
                    body_text = msg.get("body_text", "")
                    if body_text:
                        last_customer_message = body_text
                        break
        
        # Fallback to last_message if no customer message found
        if not last_customer_message and "last_message" in ticket_data:
            last_msg = ticket_data.get("last_message", {})
            if not last_msg.get("from_agent", True):
                last_customer_message = last_msg.get("body_text", "")
        
        # Extract order number from tags or subject
        order_number = None
        tags = ticket_data.get("tags", [])
        
        for tag in tags:
            if isinstance(tag, dict):
                tag_name = tag.get("name", "")
            else:
                tag_name = str(tag)
            
            # Look for order numbers (Freebird: 102xxxxxx, Simple: 203xxxxx)
            if tag_name.startswith("102") and len(tag_name) == 9:
                order_number = tag_name
                break
            elif tag_name.startswith("203") and len(tag_name) == 8:
                order_number = tag_name
                break
        
        # Try to find in subject if not in tags
        if not order_number:
            subject = ticket_data.get("subject") or ""
            if subject:
                order_match = re.search(r"\b(102\d{6}|203\d{5})\b", subject)
                if order_match:
                    order_number = order_match.group(1)
        
        # Build ticket record
        ticket = {
            "ticket_id": ticket_id,
            "subject": ticket_data.get("subject", ""),
            "customer_name": customer_name,
            "customer_email": customer.get("email", "") if customer else "",
            "order_number": order_number,
            "channel": ticket_data.get("channel", "email"),
            "last_customer_message": last_customer_message,
            "metadata": {
                "status": ticket_data.get("status", ""),
                "via": ticket_data.get("via", ""),
                "language": ticket_data.get("language", ""),
                "assignee_user_id": ticket_data.get("assignee_user", {}).get("id") if ticket_data.get("assignee_user") else None,
                "synced_at": datetime.utcnow().isoformat()
            },
            "created_at": ticket_data.get("created_datetime", datetime.utcnow().isoformat()),
            "updated_at": ticket_data.get("updated_datetime", datetime.utcnow().isoformat())
        }
        
        return ticket

    def sync_ticket(self, ticket_id: str) -> bool:
        """
        Sync a single ticket from Gorgias
        
        Args:
            ticket_id: Ticket ID to sync
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Syncing ticket {ticket_id}")
            
            # Fetch ticket data
            ticket_data = self._make_request(f"tickets/{ticket_id}")
            
            if not ticket_data:
                logger.error(f"Failed to fetch ticket {ticket_id}")
                return False
            
            # Also fetch messages
            messages_data = self._make_request(f"tickets/{ticket_id}/messages")
            if messages_data and "data" in messages_data:
                ticket_data["messages"] = messages_data["data"]
            
            # Extract and store
            ticket = self._extract_ticket_info(ticket_data)
            success = self.db.upsert_ticket(ticket)
            
            if success:
                logger.info(f"✅ Synced ticket {ticket_id}")
            else:
                logger.error(f"❌ Failed to store ticket {ticket_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing ticket {ticket_id}: {e}", exc_info=True)
            return False

    def sync_recent_tickets(self, limit: int = 20, fetch_messages: bool = False) -> int:
        """
        Sync recent tickets from Gorgias
        
        Args:
            limit: Maximum number of tickets to sync
            fetch_messages: Whether to fetch individual messages (causes rate limiting)
            
        Returns:
            Number of tickets successfully synced
        """
        try:
            logger.info(f"Syncing up to {limit} recent tickets (fetch_messages={fetch_messages})")
            
            # Fetch recent tickets (messages need to be fetched separately)
            params = {
                "order_by": "updated_datetime:desc",
                "limit": min(limit, 50)  # Cap at 50 to avoid rate limits
            }
            
            response = self._make_request("tickets", params=params)
            
            if not response or "data" not in response:
                logger.error("Failed to fetch recent tickets")
                return 0
            
            tickets = response["data"]
            logger.info(f"Fetched {len(tickets)} tickets from Gorgias")
            
            synced_count = 0
            rate_limit_wait = 1.0  # Wait 1 second between message fetches to avoid rate limits
            
            for i, ticket_data in enumerate(tickets):
                try:
                    ticket_id = str(ticket_data.get("id", ""))
                    if not ticket_id:
                        continue
                    
                    # Fetch messages for each ticket (with rate limiting)
                    # Only fetch if we don't already have messages or if explicitly requested
                    if "messages" not in ticket_data or not ticket_data.get("messages"):
                        # Add delay to avoid rate limiting (skip first one)
                        if i > 0:
                            time.sleep(rate_limit_wait)
                        
                        messages_data = self._make_request(f"tickets/{ticket_id}/messages")
                        if messages_data and "data" in messages_data:
                            ticket_data["messages"] = messages_data["data"]
                        else:
                            # If we can't fetch messages, skip this ticket
                            logger.warning(f"Could not fetch messages for ticket {ticket_id}, skipping")
                            continue
                    
                    # Extract and store
                    ticket = self._extract_ticket_info(ticket_data)
                    
                    if self.db.upsert_ticket(ticket):
                        synced_count += 1
                    
                    # Progress logging every 10 tickets
                    if (i + 1) % 10 == 0:
                        logger.info(f"Progress: {i + 1}/{len(tickets)} tickets processed")
                    
                except Exception as e:
                    logger.error(f"Error processing ticket {ticket_data.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Successfully synced {synced_count}/{len(tickets)} tickets")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing recent tickets: {e}", exc_info=True)
            return 0

    def sync_tickets_by_status(self, status: str = "open", limit: int = 50) -> int:
        """
        Sync tickets by status
        
        Args:
            status: Ticket status (open, closed, etc.)
            limit: Maximum number of tickets
            
        Returns:
            Number of tickets synced
        """
        try:
            logger.info(f"Syncing {status} tickets (limit: {limit})")
            
            params = {
                "status": status,
                "order_by": "updated_datetime:desc",
                "limit": limit
            }
            
            response = self._make_request("tickets", params=params)
            
            if not response or "data" not in response:
                logger.error(f"Failed to fetch {status} tickets")
                return 0
            
            tickets = response["data"]
            synced_count = 0
            
            for ticket_data in tickets:
                try:
                    ticket_id = str(ticket_data.get("id", ""))
                    if not ticket_id:
                        continue
                    
                    # Fetch messages
                    messages_data = self._make_request(f"tickets/{ticket_id}/messages")
                    if messages_data and "data" in messages_data:
                        ticket_data["messages"] = messages_data["data"]
                    
                    ticket = self._extract_ticket_info(ticket_data)
                    
                    if self.db.upsert_ticket(ticket):
                        synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing ticket: {e}")
                    continue
            
            logger.info(f"✅ Synced {synced_count} {status} tickets")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing {status} tickets: {e}", exc_info=True)
            return 0

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        return {
            "auth_configured": bool(self.gorgias_auth),
            "base_url": self.gorgias_base_url,
            "tickets_in_db": self.db.get_ticket_count(),
            "suggestions_in_db": self.db.get_suggestion_count()
        }


# Singleton instance
_sync_instance = None


def get_sync() -> TicketSync:
    """Get or create ticket sync instance"""
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = TicketSync()
        logger.info("Ticket sync instance created")
    return _sync_instance

