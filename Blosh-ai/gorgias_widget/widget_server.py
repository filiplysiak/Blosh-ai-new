"""
Backend server that provides AI suggestions to Gorgias widget
"""

import os
import sys

# Configuration - SET BEFORE IMPORTS
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
GORGIAS_BASE_URL = 'https://freebirdicons.gorgias.com/api'

# Set environment variable BEFORE importing
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_chats_gorgias', 'Data_collection_new'))

# Now import after env is set
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from improved_response_generator import generate_response
import requests
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache = {}

def get_ticket_info(ticket_id):
    """Fetch ticket from Gorgias API"""
    try:
        url = f"{GORGIAS_BASE_URL}/tickets/{ticket_id}"
        headers = {'authorization': GORGIAS_AUTH}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            customer = data.get('customer', {})
            customer_name = customer.get('firstname', '') or (customer.get('name', '').split()[0] if customer.get('name') else '')
            
            # Get last customer message
            messages = data.get('messages', [])
            last_message = ''
            for msg in reversed(messages):
                if msg.get('source', {}).get('type') == 'customer':
                    last_message = msg.get('body_text', '')
                    break
            
            # Extract order number
            order_number = None
            for tag in data.get('tags', []):
                tag_name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
                if tag_name.startswith('102') or tag_name.startswith('203'):
                    order_number = tag_name
                    break
            
            if not order_number:
                match = re.search(r'\b(102\d{6}|203\d{5})\b', data.get('subject', ''))
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
        logger.error(f"Error fetching ticket: {str(e)}")
        return None

@app.route('/api/widget/<ticket_id>', methods=['GET'])
def widget_data(ticket_id):
    """Widget endpoint - returns AI suggestion for Gorgias"""
    
    try:
        logger.info(f"Widget request for ticket {ticket_id}")
        
        # Check cache
        if ticket_id in cache:
            return jsonify(cache[ticket_id])
        
        # Fetch ticket
        ticket_info = get_ticket_info(ticket_id)
        
        if not ticket_info or not ticket_info['message']:
            return jsonify({
                'suggestion': 'Waiting for customer message...',
                'quality_score': '0',
                'confidence': 'N/A',
                'brand': 'N/A'
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
                'quality_score': '0',
                'confidence': 'Error',
                'brand': 'N/A'
            })
        
        # Format for Gorgias widget
        response_data = {
            'suggestion': result['response'],
            'quality_score': f"{result['quality_score']}%",
            'confidence': 'High ✓' if result['quality_score'] >= 70 else 'Medium ⚠' if result['quality_score'] >= 50 else 'Low ✗',
            'brand': result['brand']
        }
        
        cache[ticket_id] = response_data
        
        logger.info(f"Generated suggestion for {ticket_id} - Quality: {result['quality_score']}%")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({
            'suggestion': f'Error: {str(e)}',
            'quality_score': '0',
            'confidence': 'Error',
            'brand': 'N/A'
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    logger.info("🚀 Gorgias Widget Server Starting...")
    logger.info(f"Endpoints:")
    logger.info(f"  GET /api/widget/<ticket_id>  - Widget data")
    logger.info(f"  GET /health                   - Health check")
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

