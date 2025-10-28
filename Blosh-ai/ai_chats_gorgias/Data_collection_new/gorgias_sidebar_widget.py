"""
Gorgias Sidebar Widget - AI Response Suggestions
Returns data in the format Gorgias expects for sidebar widgets
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from improved_response_generator import generate_response
import requests
import re

app = Flask(__name__)
CORS(app)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
GORGIAS_BASE_URL = 'https://freebirdicons.gorgias.com/api'

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for suggestions
cache = {}

# ============================================================================
# GORGIAS API HELPERS
# ============================================================================

def get_ticket_info(ticket_id):
    """Fetch ticket info from Gorgias"""
    try:
        url = f"{GORGIAS_BASE_URL}/tickets/{ticket_id}"
        headers = {
            'authorization': GORGIAS_AUTH,
            'accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract customer info
            customer = data.get('customer', {})
            customer_name = customer.get('firstname', '') or customer.get('name', '').split()[0] if customer.get('name') else ''
            
            # Get last customer message
            messages = data.get('messages', [])
            last_message = ''
            
            for msg in reversed(messages):
                if msg.get('source', {}).get('type') == 'customer':
                    last_message = msg.get('body_text', '')
                    break
            
            # Get order number from tags or subject
            order_number = None
            tags = data.get('tags', [])
            for tag in tags:
                tag_name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
                if tag_name.startswith('102') or tag_name.startswith('203'):
                    order_number = tag_name
                    break
            
            # Try subject if no order in tags
            if not order_number:
                subject = data.get('subject', '')
                match = re.search(r'\b(102\d{6}|203\d{5})\b', subject)
                if match:
                    order_number = match.group(1)
            
            return {
                'customer_name': customer_name,
                'message': last_message,
                'order_number': order_number,
                'subject': data.get('subject', '')
            }
        else:
            logger.error(f"Failed to fetch ticket {ticket_id}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching ticket info: {str(e)}")
        return None

# ============================================================================
# MAIN WIDGET ENDPOINT - This is what Gorgias calls
# ============================================================================

@app.route('/api/widget/<ticket_id>', methods=['GET'])
def widget_data(ticket_id):
    """
    Returns widget data in Gorgias format
    
    This endpoint is called by Gorgias to display data in the sidebar
    URL in Gorgias: https://your-app.railway.app/api/widget/{{ticket.id}}
    """
    
    try:
        logger.info(f"Widget request for ticket {ticket_id}")
        
        # Check cache
        if ticket_id in cache:
            logger.info(f"Returning cached suggestion for {ticket_id}")
            return jsonify(cache[ticket_id])
        
        # Fetch ticket info from Gorgias
        ticket_info = get_ticket_info(ticket_id)
        
        if not ticket_info or not ticket_info['message']:
            return jsonify({
                'suggestion': 'No customer message found yet. AI will suggest a response when customer sends a message.',
                'quality_score': 0,
                'status': 'waiting'
            })
        
        # Generate AI suggestion
        result = generate_response(
            customer_message=ticket_info['message'],
            customer_name=ticket_info['customer_name'],
            order_number=ticket_info['order_number'],
            subject=ticket_info['subject']
        )
        
        if not result:
            return jsonify({
                'suggestion': 'Error generating suggestion',
                'quality_score': 0,
                'status': 'error'
            }), 500
        
        # Format response for Gorgias widget
        widget_response = {
            'suggestion': result['response'],
            'quality_score': result['quality_score'],
            'brand': result['brand'],
            'confidence': 'High' if result['quality_score'] >= 70 else 'Medium' if result['quality_score'] >= 50 else 'Low',
            'warnings': result.get('warnings', []),
            'status': 'ready'
        }
        
        # Cache it
        cache[ticket_id] = widget_response
        
        logger.info(f"Generated suggestion for {ticket_id} - Quality: {result['quality_score']}%")
        
        return jsonify(widget_response)
        
    except Exception as e:
        logger.error(f"Error in widget_data: {str(e)}", exc_info=True)
        return jsonify({
            'suggestion': f'Error: {str(e)}',
            'quality_score': 0,
            'status': 'error'
        }), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'widget': '/api/widget/<ticket_id>',
            'health': '/health'
        }
    })

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Gorgias Sidebar Widget Server")
    logger.info("="*60)
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health                    - Health check")
    logger.info("  GET  /api/widget/<ticket_id>    - Widget data for Gorgias sidebar")
    logger.info("")
    logger.info("Configure in Gorgias:")
    logger.info("  Settings → App Store → HTTP Integration")
    logger.info("  URL: https://your-app.railway.app/api/widget/{{ticket.id}}")
    logger.info("")
    logger.info("="*60)
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

