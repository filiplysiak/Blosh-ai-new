"""
Gorgias Widget API Server (database-backed)
Provides AI response suggestions for Gorgias tickets using a fine-tuned model.

Version: 3.1
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

from database import get_db
from improved_response_generator import FINETUNED_MODEL_ID
from suggestion_manager import get_manager
from ticket_sync import get_sync

# --------------------------------------------------------------------------- #
# Flask & configuration
# --------------------------------------------------------------------------- #

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["https://*.gorgias.com", "https://freebirdicons.gorgias.com"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    },
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

db = get_db()
sync = get_sync()
manager = get_manager()

scheduler = BackgroundScheduler()
initialization_done = False

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def start_thread(target, *args, **kwargs) -> threading.Thread:
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


def parse_payload(raw_data: Any) -> Dict[str, Any]:
    if isinstance(raw_data, dict):
        return raw_data

    if isinstance(raw_data, list):
        if raw_data and isinstance(raw_data[0], dict) and "key" in raw_data[0] and "value" in raw_data[0]:
            return {entry.get("key"): entry.get("value") for entry in raw_data if isinstance(entry, dict)}
        if raw_data and isinstance(raw_data[0], dict):
            return raw_data[0]

    return {}


def choose_value(*candidates: Any) -> Optional[Any]:
    for value in candidates:
        if value not in (None, "", []):
            return value
    return None


def upsert_ticket_from_payload(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ticket_id = str(choose_value(data.get("ticket_id"), data.get("id"), "")).strip()
    if not ticket_id:
        return None

    existing = db.get_ticket(ticket_id)

    metadata = {}
    if existing and existing.get("metadata"):
        metadata.update(existing["metadata"])
    metadata.update(data.get("metadata") or {})
    if "source" not in metadata:
        metadata["source"] = "api"

    ticket_record = {
        "ticket_id": ticket_id,
        "subject": choose_value(data.get("subject"), existing.get("subject") if existing else None),
        "customer_name": choose_value(
            data.get("customer_name"),
            data.get("customerFirstname"),
            data.get("customer_first_name"),
            existing.get("customer_name") if existing else None,
        ),
        "customer_email": choose_value(
            data.get("customer_email"),
            data.get("customerEmail"),
            existing.get("customer_email") if existing else None,
        ),
        "order_number": choose_value(
            data.get("order_number"),
            data.get("order"),
            existing.get("order_number") if existing else None,
        ),
        "channel": choose_value(
            data.get("channel"),
            existing.get("channel") if existing else None,
        ),
        "last_customer_message": choose_value(
            data.get("message"),
            data.get("body_text"),
            existing.get("last_customer_message") if existing else None,
        ),
        "metadata": metadata,
        "created_at": choose_value(
            data.get("created_at"),
            data.get("created_datetime"),
            existing.get("created_at") if existing else None,
            datetime.utcnow().isoformat(),
        ),
        "updated_at": datetime.utcnow().isoformat(),
    }

    db.upsert_ticket(ticket_record)
    return db.get_ticket(ticket_id)


def format_suggestion(suggestion: Dict[str, Any], cached: bool = True) -> Dict[str, Any]:
    return {
        "ticket_id": suggestion["ticket_id"],
        "suggestion": suggestion["suggestion_text"],
        "quality_score": suggestion.get("quality_score"),
        "confidence": suggestion.get("confidence"),
        "brand": suggestion.get("brand"),
        "warnings": suggestion.get("warnings", []),
        "approved": suggestion.get("approved"),
        "timestamp": suggestion.get("generated_at"),
        "model_id": suggestion.get("model_id", FINETUNED_MODEL_ID),
        "cached": cached,
    }


def initialize_system() -> None:
    global initialization_done

    if initialization_done:
        logger.info("Initialization already complete")
        return

    logger.info("=" * 60)
    logger.info("🚀 Initializing widget backend")
    logger.info("=" * 60)

    try:
        # Check if GORGIAS_AUTH is set
        gorgias_auth = os.getenv("GORGIAS_AUTH")
        if not gorgias_auth:
            logger.warning("⚠️  GORGIAS_AUTH not set - skipping ticket sync")
            logger.info("Widget will work for on-demand generation only")
            initialization_done = True
            return
        
        ticket_count = db.get_ticket_count()
        logger.info("Database currently has %s tickets", ticket_count)

        # Sync recent tickets to catch active conversations
        # Each ticket requires 2 API calls (1 for ticket, 1 for messages)
        # With 1 second delay, 15 tickets = ~30 seconds
        if ticket_count < 10:
            synced = sync.sync_recent_tickets(limit=20, fetch_messages=False)
        else:
            synced = sync.sync_recent_tickets(limit=15, fetch_messages=False)
        logger.info("Synced %s tickets during initialization", synced)

        summary = manager.ensure_suggestions_for_top_n()
        logger.info("Ensured top tickets have suggestions: %s", summary)

        stats = db.get_stats()
        logger.info("Stats: %s", stats)

        initialization_done = True
        logger.info("✅ Initialization complete")

    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Initialization failed: %s", exc, exc_info=True)
        # Don't crash - let the server start anyway
        initialization_done = True


def periodic_sync() -> None:
    try:
        # Check if GORGIAS_AUTH is set
        if not os.getenv("GORGIAS_AUTH"):
            logger.debug("Skipping periodic sync - GORGIAS_AUTH not set")
            return
            
        logger.info("Running periodic sync...")
        # Sync more tickets to catch recent activity (15 tickets = ~30 seconds with delays)
        synced = sync.sync_recent_tickets(limit=15, fetch_messages=False)
        summary = manager.ensure_suggestions_for_top_n()
        logger.info("Periodic sync results - synced: %s, summary: %s", synced, summary)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error during periodic sync: %s", exc, exc_info=True)


def startup() -> None:
    try:
        logger.info("🚀 Starting background tasks...")
        start_thread(initialize_system)
        if not scheduler.running:
            scheduler.add_job(periodic_sync, "interval", minutes=10, id="periodic_sync")
            scheduler.start()
            logger.info("✅ Scheduled periodic sync every 10 minutes")
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Don't crash - let Flask start


# Run startup at import time (works with gunicorn)
# Delay startup to after Flask is ready
def delayed_startup():
    import time
    time.sleep(2)  # Give Flask time to bind to port
    try:
        startup()
        logger.info("✅ App initialization complete")
    except Exception as e:
        logger.error(f"Failed during startup: {e}", exc_info=True)

# Start in background thread so Flask can bind immediately
import threading
threading.Thread(target=delayed_startup, daemon=True).start()
logger.info("✅ Flask app module loaded - healthcheck endpoint ready")

# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@app.route("/", methods=["GET"])
def root() -> Any:
    stats = db.get_stats()
    return jsonify(
        {
            "status": "healthy",
            "service": "Gorgias AI Widget API",
            "version": "3.0",
            "model_id": FINETUNED_MODEL_ID,
            "initialized": initialization_done,
            "database": stats,
            "endpoints": {
                "health": "/health",
                "stats": "/api/stats",
                "suggest": "/api/suggest",
                "suggest_get": "/api/suggest/<ticket_id>",
                "widget": "/widget/<ticket_id>",
                "sync": "/api/sync",
            },
        }
    )


@app.route("/health", methods=["GET"])
def health() -> Any:
    stats = db.get_stats()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "initialized": initialization_done,
            "database": stats,
        }
    )


@app.route("/api/stats", methods=["GET"])
def get_stats() -> Any:
    stats = db.get_stats()
    top_tickets = manager.get_top_n_tickets()
    return jsonify(
        {
            "database": stats,
            "top_tickets": [
                {
                    "ticket_id": ticket["ticket_id"],
                    "created_at": ticket.get("created_at"),
                    "subject": ticket.get("subject"),
                    "customer_name": ticket.get("customer_name"),
                    "has_suggestion": db.has_suggestion(ticket["ticket_id"]),
                }
                for ticket in top_tickets
            ],
        }
    )


@app.route("/api/suggestions", methods=["GET"])
def list_suggestions() -> Any:
    """List all suggestions with their tickets"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.ticket_id,
                    s.suggestion_text,
                    s.quality_score,
                    s.brand,
                    s.generated_at,
                    t.subject,
                    t.customer_name
                FROM suggestions s
                LEFT JOIN tickets t ON s.ticket_id = t.ticket_id
                WHERE s.ticket_id NOT LIKE 'test_%'
                ORDER BY s.generated_at DESC
                LIMIT 50
            """)
            
            suggestions = []
            for row in cursor.fetchall():
                suggestions.append({
                    "ticket_id": row[0],
                    "suggestion_preview": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                    "quality_score": row[2],
                    "brand": row[3],
                    "generated_at": row[4],
                    "subject": row[5],
                    "customer_name": row[6],
                    "view_url": f"/api/suggest/{row[0]}",
                    "widget_url": f"/widget/{row[0]}"
                })
            
            return jsonify({
                "total": len(suggestions),
                "suggestions": suggestions
            })
    except Exception as e:
        logger.error(f"Error listing suggestions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ticket/<ticket_id>", methods=["GET"])
def get_ticket_info(ticket_id: str) -> Any:
    """Get detailed ticket information for debugging"""
    try:
        # Check if ticket exists in database
        ticket = db.get_ticket(ticket_id)
        suggestion = db.get_suggestion(ticket_id)
        
        # Check queue status
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, priority, queued_at, started_at, completed_at, error
                FROM generation_queue
                WHERE ticket_id = ?
            """, (ticket_id,))
            queue_row = cursor.fetchone()
            queue_status = dict(queue_row) if queue_row else None
        
        return jsonify({
            "ticket_id": ticket_id,
            "in_database": ticket is not None,
            "has_suggestion": suggestion is not None,
            "ticket_data": ticket,
            "suggestion_data": {
                "quality_score": suggestion.get("quality_score") if suggestion else None,
                "brand": suggestion.get("brand") if suggestion else None,
                "generated_at": suggestion.get("generated_at") if suggestion else None,
            } if suggestion else None,
            "queue_status": queue_status,
            "actions": {
                "sync_ticket": f"POST /api/sync-ticket/{ticket_id}",
                "generate_suggestion": f"POST /api/suggest with ticket_id={ticket_id}"
            }
        })
    except Exception as e:
        logger.error(f"Error getting ticket info: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync-ticket/<ticket_id>", methods=["POST"])
def sync_single_ticket(ticket_id: str) -> Any:
    """Sync a specific ticket from Gorgias and generate suggestion"""
    try:
        logger.info(f"Manual sync requested for ticket {ticket_id}")
        
        # Sync the ticket
        success = sync.sync_ticket(ticket_id)
        
        if not success:
            return jsonify({
                "status": "error",
                "message": f"Failed to sync ticket {ticket_id} from Gorgias"
            }), 500
        
        # Queue for suggestion generation
        manager.generate_suggestion_async(ticket_id, priority=100)  # High priority
        
        return jsonify({
            "status": "success",
            "message": f"Ticket {ticket_id} synced and queued for generation",
            "ticket_id": ticket_id,
            "check_status": f"/api/ticket/{ticket_id}"
        })
        
    except Exception as e:
        logger.error(f"Error syncing ticket {ticket_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cleanup-test-data", methods=["POST"])
def cleanup_test_data_endpoint() -> Any:
    """Remove test data from database"""
    try:
        logger.info("Cleanup test data requested via API")
        
        with db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Find test tickets
            cursor.execute("SELECT ticket_id FROM tickets WHERE ticket_id LIKE 'test_%'")
            test_tickets = [row[0] for row in cursor.fetchall()]
            
            if not test_tickets:
                return jsonify({
                    "status": "success",
                    "message": "No test data found - database is clean!",
                    "deleted": {
                        "tickets": 0,
                        "suggestions": 0,
                        "queue": 0,
                        "feedback": 0
                    }
                })
            
            # Delete test data
            cursor.execute("DELETE FROM suggestions WHERE ticket_id LIKE 'test_%'")
            deleted_suggestions = cursor.rowcount
            
            cursor.execute("DELETE FROM generation_queue WHERE ticket_id LIKE 'test_%'")
            deleted_queue = cursor.rowcount
            
            cursor.execute("DELETE FROM feedback WHERE ticket_id LIKE 'test_%'")
            deleted_feedback = cursor.rowcount
            
            cursor.execute("DELETE FROM tickets WHERE ticket_id LIKE 'test_%'")
            deleted_tickets = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"Cleanup complete: {deleted_tickets} tickets, {deleted_suggestions} suggestions removed")
            
            return jsonify({
                "status": "success",
                "message": f"Removed {deleted_tickets} test tickets",
                "deleted": {
                    "tickets": deleted_tickets,
                    "suggestions": deleted_suggestions,
                    "queue": deleted_queue,
                    "feedback": deleted_feedback
                },
                "test_tickets_removed": test_tickets
            })
            
    except Exception as e:
        logger.error(f"Error cleaning up test data: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/init", methods=["POST"])
def trigger_init() -> Any:
    global initialization_done
    initialization_done = False
    start_thread(initialize_system)
    return jsonify({"status": "initialization_started"})


@app.route("/api/sync", methods=["POST"])
def trigger_sync() -> Any:
    data = parse_payload(request.get_json()) if request.get_json() else {}
    limit = int(choose_value(data.get("limit"), 20))
    fetch_messages = data.get("fetch_messages", False)

    def run_sync():
        synced = sync.sync_recent_tickets(limit=min(limit, 50), fetch_messages=fetch_messages)
        summary = manager.ensure_suggestions_for_top_n()
        logger.info("Manual sync complete - synced: %s summary: %s", synced, summary)

    start_thread(run_sync)
    return jsonify({"status": "sync_started", "limit": limit, "fetch_messages": fetch_messages})


@app.route("/api/suggest/<ticket_id>", methods=["GET"])
def get_suggestion(ticket_id: str) -> Any:
    suggestion = db.get_suggestion(ticket_id)
    if not suggestion:
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "ticket_id": ticket_id,
                    "message": "Suggestion not ready yet",
                }
            ),
            404,
        )

    return jsonify(format_suggestion(suggestion))


@app.route("/api/widget-data/<ticket_id>", methods=["GET"])
def widget_data(ticket_id: str) -> Any:
    """
    Gorgias widget data endpoint - returns JSON for widget display
    This is called by Gorgias HTTP integration when widget loads
    """
    logger.info("Widget data request for ticket %s", ticket_id)
    
    # Check if suggestion exists in database
    suggestion = db.get_suggestion(ticket_id)
    
    if suggestion:
        # Return pre-generated suggestion (INSTANT)
        logger.info("Returning pre-generated suggestion for ticket %s", ticket_id)
        return jsonify({
            "Status": "ready",
            ":": f"Quality: {suggestion.get('quality_score', 0)}% | Brand: {suggestion.get('brand', 'Unknown')}",
            "Suggested Response": suggestion['suggestion_text'],
            "Quality Score": f"{suggestion.get('quality_score', 0)}%",
            "Brand": suggestion.get('brand', 'Unknown'),
            "Generated At": suggestion.get('generated_at', '')
        })
    else:
        # No suggestion yet - check if ticket exists
        ticket = db.get_ticket(ticket_id)
        
        if not ticket:
            # Try to sync from Gorgias
            logger.info("Ticket %s not in DB, syncing from Gorgias", ticket_id)
            synced = sync.sync_ticket(ticket_id)
            if synced:
                ticket = db.get_ticket(ticket_id)

        if not ticket:
            # Still no ticket after sync attempt
            logger.warning("Ticket %s not found even after sync attempt", ticket_id)
            return jsonify({
                "Status": "not_found",
                ":": "Ticket not found in database",
                "Suggested Response": "-",
                "Quality Score": "-",
                "Brand": "-",
                "Generated At": "-"
            })

        # Check if this ticket should have AI suggestions
        channel = ticket.get('channel', '').lower()
        is_email_ticket = 'email' in channel
        has_customer_message = bool(ticket.get('last_customer_message'))

        # For email tickets, be more permissive
        if is_email_ticket:
            # Allow email tickets even without customer messages (for follow-ups, etc.)
            logger.info("Processing email ticket %s (channel: %s, has_customer_msg: %s)",
                       ticket_id, channel, has_customer_message)
        elif not has_customer_message:
            # For non-email tickets, still require customer message
            logger.warning("Non-email ticket %s has no customer message", ticket_id)
            return jsonify({
                "Status": "no_message",
                ":": "No customer inquiry detected",
                "Suggested Response": "-",
                "Quality Score": "-",
                "Brand": "-",
                "Generated At": "-"
            })

        # Queue for generation if not already queued
        logger.info("Queueing suggestion generation for ticket %s", ticket_id)
        manager.generate_suggestion_async(ticket_id)
        
        return jsonify({
            "Status": "generating",
            ":": "AI suggestion is being generated. Refresh the page in 10-15 seconds.",
            "Suggested Response": "-",
            "Quality Score": "-",
            "Brand": "-",
            "Generated At": "-"
        })


@app.route("/api/suggest", methods=["POST"])
def create_suggestion() -> Any:
    data = parse_payload(request.get_json())
    ticket_id = choose_value(data.get("ticket_id"), data.get("id"))

    if not ticket_id:
        return jsonify({"error": "ticket_id required"}), 400

    ticket = upsert_ticket_from_payload(data)
    if not ticket:
        ticket = db.get_ticket(str(ticket_id))

    existing = db.get_suggestion(str(ticket_id))
    if existing:
        return jsonify(format_suggestion(existing))

    manager.generate_suggestion_async(str(ticket_id))
    return (
        jsonify(
            {
                "status": "accepted",
                "ticket_id": ticket_id,
                "message": "Generation started",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        202,
    )


@app.route("/api/feedback", methods=["POST"])
def record_feedback() -> Any:
    data = parse_payload(request.get_json())
    ticket_id = data.get("ticket_id")
    feedback = data.get("feedback")

    logger.info("Feedback received for ticket %s: %s", ticket_id, feedback)
    # TODO: Persist feedback if needed.
    return jsonify({"status": "success"})


@app.route("/api/setup-widget", methods=["POST"])
def setup_gorgias_widget() -> Any:
    """Set up the Gorgias widget via API."""
    try:
        import requests
        import os

        # Get Gorgias credentials
        auth = os.getenv("GORGIAS_AUTH")
        base_url = os.getenv("GORGIAS_BASE_URL", "https://freebirdicons.gorgias.com/api")

        if not auth:
            return jsonify({
                "status": "error",
                "message": "GORGIAS_AUTH not configured"
            }), 500

        # Widget configuration
        widget_data = {
            "name": "AI Response Suggestion",
            "description": "AI-powered response suggestions for customer support tickets",
            "type": "custom_html",
            "position": "right_sidebar",
            "settings": {
                "html": f'''<iframe
  src="{request.host_url.rstrip('/')}/widget/{{{{ticket.id}}}}"
  width="100%"
  height="700px"
  frameborder="0"
  style="border: none; min-height: 700px;"
></iframe>'''
            },
            "display_conditions": [
                {
                    "type": "ticket_status",
                    "operator": "is_not",
                    "value": "closed"
                }
            ],
            "enabled": True
        }

        # Make request to Gorgias API
        url = f"{base_url.rstrip('/')}/widgets"
        headers = {
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(url, headers=headers, json=widget_data)

        if response.status_code == 201:
            result = response.json()
            logger.info("Widget created successfully: %s", result.get("id"))
            return jsonify({
                "status": "success",
                "message": "Widget created successfully",
                "widget_id": result.get("id")
            })
        else:
            error_msg = response.text
            logger.error("Failed to create widget: %s", error_msg)
            return jsonify({
                "status": "error",
                "message": f"Failed to create widget: {error_msg}"
            }), 500

    except Exception as e:
        logger.error("Error setting up widget: %s", e, exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal error: {str(e)}"
        }), 500


@app.route("/widget/<ticket_id>", methods=["GET", "POST"])
def widget(ticket_id: str) -> Any:
    if request.method == "POST":
        logger.info("Widget POST for ticket %s", ticket_id)
        data = parse_payload(request.get_json())
        upsert_ticket_from_payload({"ticket_id": ticket_id, **data})

        if not db.has_suggestion(ticket_id):
            manager.generate_suggestion_async(ticket_id)

        return jsonify(
            {
                "status": "queued",
                "ticket_id": ticket_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    widget_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Suggestion</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            padding: 16px;
            background: #f8f9fa;
            font-size: 14px;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
        }
        .header h3 {
            color: #2c3e50;
            font-size: 16px;
        }
        .loading, .no-suggestion {
            text-align: center;
            padding: 24px 16px;
            color: #6c757d;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #2196f3;
            border-radius: 50%;
            width: 34px;
            height: 34px;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .suggestion-box {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .suggestion-text {
            background: #e7f3ff;
            border-left: 4px solid #2196f3;
            padding: 12px;
            border-radius: 4px;
            white-space: pre-wrap;
            font-size: 13px;
            line-height: 1.6;
            color: #212529;
            max-height: 360px;
            overflow-y: auto;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-high { background: #d4edda; color: #155724; }
        .badge-medium { background: #fff3cd; color: #856404; }
        .badge-low { background: #f8d7da; color: #721c24; }
        .brand-tag {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }
        .actions {
            display: flex;
            gap: 8px;
        }
        .btn {
            flex: 1;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #2196f3;
            color: white;
        }
        .btn-primary:hover {
            background: #1976d2;
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(33,150,243,0.3);
        }
        .btn-secondary {
            background: #e9ecef;
            color: #495057;
        }
        .btn-secondary:hover {
            background: #dee2e6;
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            font-size: 12px;
            color: #856404;
            border-radius: 4px;
        }
        .info {
            display: flex;
            justify-content: space-between;
            color: #6c757d;
            font-size: 12px;
        }
        .feedback {
            padding-top: 12px;
            border-top: 1px solid #e9ecef;
            text-align: center;
        }
        .feedback-btns {
            display: flex;
            justify-content: center;
            gap: 6px;
        }
        .feedback-btn {
            padding: 6px 12px;
            font-size: 12px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            cursor: pointer;
        }
        .feedback-btn.active {
            background: #2196f3;
            color: white;
            border-color: #2196f3;
        }
        .toast {
            position: fixed;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(33, 150, 243, 0.95);
            color: white;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 12px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            z-index: 9999;
        }
        .toast.show {
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="header">
        <h3>🤖 AI Suggestion</h3>
    </div>
    <div id="content">
        <div class="loading">
            <div class="spinner"></div>
            <div>Loading suggestion...</div>
        </div>
    </div>
    <div id="toast" class="toast"></div>

    <script>
        const TICKET_ID = "{{ ticket_id }}";
        const API_BASE = window.location.origin;

        let currentSuggestion = null;
        let toastHandle = null;

        function showToast(message) {
            const toast = document.getElementById('toast');
            if (!toast) return;
            toast.textContent = message;
            toast.classList.add('show');
            if (toastHandle) {
                clearTimeout(toastHandle);
            }
            toastHandle = setTimeout(() => {
                toast.classList.remove('show');
            }, 2400);
        }

        async function loadSuggestion() {
            try {
                console.log(`Loading suggestion for ticket ${TICKET_ID}...`);
                const response = await fetch(`${API_BASE}/api/suggest/${TICKET_ID}`);

                if (response.ok) {
                    const data = await response.json();
                    console.log('Suggestion loaded successfully:', data);
                    displaySuggestion(data);
                    return;
                }

                if (response.status === 404) {
                    console.log('Suggestion not found (404), checking if generating...');
                    // Check if ticket exists and is being generated
                    const ticketCheck = await fetch(`${API_BASE}/api/ticket/${TICKET_ID}`);
                    if (ticketCheck.ok) {
                        const ticketData = await ticketCheck.json();
                        console.log('Ticket data:', ticketData);
                        
                        if (ticketData.in_database && !ticketData.has_suggestion) {
                            // Ticket exists but no suggestion yet - poll for it
                            console.log('Ticket in database, polling for suggestion...');
                            displayLoading('AI suggestion is being generated...');
                            await pollForSuggestion();
                            return;
                        }
                    }
                    
                    // Ticket doesn't exist - show generate button
                    displayNoSuggestion();
                    return;
                }

                throw new Error(`Unexpected response: ${response.status}`);
            } catch (error) {
                console.error('Error loading suggestion:', error);
                displayError(error.message || 'Failed to load suggestion');
            }
        }

        async function generateSuggestion(evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }

            displayLoading('Generating AI suggestion...');

            try {
                await fetch(`${API_BASE}/api/suggest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticket_id: TICKET_ID })
                });

                await pollForSuggestion();
            } catch (error) {
                displayError(error.message || 'Failed to generate suggestion');
            }
        }

        async function pollForSuggestion() {
            const maxAttempts = 20;  // Increased from 15
            for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                console.log(`Polling attempt ${attempt}/${maxAttempts}...`);
                
                const response = await fetch(`${API_BASE}/api/suggest/${TICKET_ID}`);
                if (response.ok) {
                    const data = await response.json();
                    console.log('Suggestion ready!', data);
                    displaySuggestion(data);
                    return;
                }
                
                displayLoading(`Generating AI suggestion... (${attempt * 2}s / ${maxAttempts * 2}s)`);
            }
            
            // Timeout - show retry button
            document.getElementById('content').innerHTML = `
                <div class="no-suggestion">
                    <div style="font-size:32px;margin-bottom:12px;">⏱️</div>
                    <div style="margin-bottom:16px;">Generation is taking longer than expected.</div>
                    <button class="btn btn-primary" onclick="loadSuggestion()">Refresh</button>
                </div>
            `;
        }

        function displayLoading(message) {
            document.getElementById('content').innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <div>${message}</div>
                </div>
            `;
        }

        function displayNoSuggestion() {
            document.getElementById('content').innerHTML = `
                <div class="no-suggestion">
                    <div style="font-size:32px;margin-bottom:12px;">💡</div>
                    <div style="margin-bottom:16px;">No AI suggestion yet for this ticket.</div>
                    <button class="btn btn-primary" onclick="generateSuggestion(event)">Generate response</button>
                </div>
            `;
        }

        function displaySuggestion(data) {
            if (!data || !data.suggestion) {
                displayNoSuggestion();
                return;
            }

            currentSuggestion = data;

            const quality = data.quality_score || 0;
            const badgeClass = quality >= 70 ? 'badge-high' : quality >= 50 ? 'badge-medium' : 'badge-low';
            const badgeLabel = quality >= 70 ? 'High' : quality >= 50 ? 'Medium' : 'Low';

            const warnings = (data.warnings || []).map(item => `<div>• ${escapeHtml(item)}</div>`).join('');
            const warningsHtml = warnings ? `<div class="warning"><strong>Review:</strong>${warnings}</div>` : '';

            document.getElementById('content').innerHTML = `
                <div class="suggestion-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="brand-tag">${escapeHtml(data.brand || 'Freebird Icons')}</span>
                        <span class="badge ${badgeClass}">${badgeLabel} quality (${Math.round(quality)}%)</span>
                    </div>
                    ${warningsHtml}
                    <div class="suggestion-text">${escapeHtml(data.suggestion)}</div>
                    <div class="actions">
                        <button class="btn btn-primary" onclick="useSuggestion(event)">Use response</button>
                        <button class="btn btn-secondary" onclick="copySuggestion(event)">Copy</button>
                        <button class="btn btn-secondary" onclick="generateSuggestion(event)">Regenerate</button>
                    </div>
                    <div class="info">
                        <div>Ticket #${escapeHtml(TICKET_ID)}</div>
                        <div>${data.cached ? 'Cached' : 'Fresh'} · Model: ${escapeHtml(data.model_id || '')}</div>
                    </div>
                    <div class="feedback">
                        <div style="margin-bottom:8px;color:#6c757d;">Feedback</div>
                        <div class="feedback-btns">
                            <button class="feedback-btn" data-feedback="used" onclick="sendFeedback('used', event)">👍 Used</button>
                            <button class="feedback-btn" data-feedback="edited" onclick="sendFeedback('edited', event)">✏️ Edited</button>
                            <button class="feedback-btn" data-feedback="ignored" onclick="sendFeedback('ignored', event)">👎 Ignored</button>
                        </div>
                    </div>
                </div>
            `;
        }

        function displayError(message) {
            document.getElementById('content').innerHTML = `
                <div class="no-suggestion">
                    <div style="font-size:32px;margin-bottom:12px;">⚠️</div>
                    <div style="margin-bottom:16px;">${escapeHtml(message)}</div>
                    <button class="btn btn-secondary" onclick="loadSuggestion()">Try again</button>
                </div>
            `;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        async function copyToClipboard(text) {
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(text);
                    return true;
                }
            } catch (err) {
                console.error('Clipboard error:', err);
            }
            return false;
        }

        async function useSuggestion(evt) {
            if (!currentSuggestion) return;
            const success = await copyToClipboard(currentSuggestion.suggestion);
            if (success) {
                showToast('Response copied. Paste into your reply field.');
                sendFeedback('used', evt);
            } else {
                displayError('Copy not supported. Please copy manually.');
            }
        }

        async function copySuggestion(evt) {
            if (!currentSuggestion) return;
            const success = await copyToClipboard(currentSuggestion.suggestion);
            if (success) {
                showToast('Copied to clipboard');
            } else {
                displayError('Copy not supported. Please copy manually.');
            }
        }

        async function sendFeedback(type, evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }

            try {
                await fetch(`${API_BASE}/api/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticket_id: TICKET_ID, feedback: type })
                });

                document.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('active'));
                if (evt && evt.currentTarget) {
                    evt.currentTarget.classList.add('active');
                }
            } catch (error) {
                console.error('Error sending feedback', error);
            }
        }

        window.addEventListener('load', loadSuggestion);
    </script>
</body>
</html>
    """

    return render_template_string(widget_html, ticket_id=ticket_id)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Running development server on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=True)

# ============================================================================
# STARTUP LOGGING (runs when gunicorn imports the module)
# ============================================================================

# ============================================================================
# RUN SERVER (only for local development)
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Running development server on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=True)

