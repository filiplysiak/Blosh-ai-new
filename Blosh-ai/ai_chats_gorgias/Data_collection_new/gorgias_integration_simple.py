"""
Gorgias Simple Integration
Automatically adds AI response suggestions as internal notes on tickets
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from improved_response_generator import generate_response
import requests

app = Flask(__name__)
CORS(app)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
GORGIAS_BASE_URL = 'https://freebirdicons.gorgias.com/api'

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# GORGIAS API FUNCTIONS
# ============================================================================

def add_internal_note(ticket_id, message):
    """Add an internal note to a Gorgias ticket"""
    try:
        url = f"{GORGIAS_BASE_URL}/tickets/{ticket_id}/messages"
        
        payload = {
            "via": "api",
            "channel": "internal-note",
            "from_agent": True,
            "body_text": message,
            "body_html": f"<p>{message.replace(chr(10), '<br>')}</p>"
        }
        
        headers = {
            'authorization': GORGIAS_AUTH,
            'content-type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            logger.info(f"✓ Added internal note to ticket {ticket_id}")
            return True
        else:
            logger.error(f"Failed to add note to ticket {ticket_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding internal note: {str(e)}")
        return False

# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@app.route('/webhook/suggest', methods=['POST'])
def webhook_suggest():
    """
    Gorgias webhook - receives ticket data and adds AI suggestion as internal note
    
    Expected from Gorgias HTTP Integration:
    {
        "ticket_id": "123",
        "customer_name": "Petra",
        "message": "Ik wil retour doen",
        "order_number": "102345678",
        "subject": "Retour"
    }
    """
    try:
        data = request.get_json()
        
        ticket_id = data.get('ticket_id')
        customer_name = data.get('customer_name', '')
        message = data.get('message', '')
        order_number = data.get('order_number', '')
        subject = data.get('subject', '')
        
        if not ticket_id or not message:
            logger.warning("Missing ticket_id or message")
            return jsonify({'error': 'Missing required fields'}), 400
        
        logger.info(f"Received webhook for ticket {ticket_id}")
        
        # Generate AI suggestion
        result = generate_response(
            customer_message=message,
            customer_name=customer_name,
            order_number=order_number,
            subject=subject
        )
        
        if not result:
            logger.error(f"Failed to generate suggestion for ticket {ticket_id}")
            return jsonify({'error': 'Failed to generate suggestion'}), 500
        
        # Format the internal note
        quality_emoji = "🟢" if result['quality_score'] >= 70 else "🟡" if result['quality_score'] >= 50 else "🔴"
        
        note_text = f"""🤖 AI SUGGESTED RESPONSE {quality_emoji}

Quality: {result['quality_score']}% | Brand: {result['brand']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{result['response']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TIP: Copy this response and paste it into your reply. Edit as needed before sending.

{('⚠️ WARNINGS: ' + ', '.join(result.get('warnings', []))) if result.get('warnings') else '✓ No quality issues detected'}"""
        
        # Add internal note to ticket
        success = add_internal_note(ticket_id, note_text)
        
        if success:
            return jsonify({
                'status': 'success',
                'ticket_id': ticket_id,
                'quality_score': result['quality_score'],
                'message': 'AI suggestion added as internal note'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to add internal note'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DIRECT API ENDPOINT (for testing or manual use)
# ============================================================================

@app.route('/api/suggest', methods=['POST'])
def api_suggest():
    """
    Direct API endpoint - just returns the suggestion as JSON
    
    Request:
    {
        "ticket_id": "123",
        "customer_name": "Petra",
        "message": "Ik wil retour doen",
        "order_number": "102345678"
    }
    
    Response:
    {
        "suggestion": "Hi Petra,...",
        "quality_score": 85,
        "brand": "Freebird Icons"
    }
    """
    try:
        data = request.get_json()
        
        customer_name = data.get('customer_name', '')
        message = data.get('message', '')
        order_number = data.get('order_number', '')
        subject = data.get('subject', '')
        
        if not message:
            return jsonify({'error': 'message is required'}), 400
        
        result = generate_response(
            customer_message=message,
            customer_name=customer_name,
            order_number=order_number,
            subject=subject
        )
        
        if not result:
            return jsonify({'error': 'Failed to generate suggestion'}), 500
        
        return jsonify({
            'suggestion': result['response'],
            'quality_score': result['quality_score'],
            'brand': result['brand'],
            'confidence': result['quality_score'],
            'warnings': result.get('warnings', []),
            'approved': result['approved']
        })
        
    except Exception as e:
        logger.error(f"Error in api_suggest: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model': 'ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB'
    })

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Gorgias AI Integration Server (Simple)")
    logger.info("="*60)
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health                - Health check")
    logger.info("  POST /webhook/suggest       - Gorgias webhook (adds internal note)")
    logger.info("  POST /api/suggest           - Direct API (returns JSON)")
    logger.info("")
    logger.info("="*60)
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

