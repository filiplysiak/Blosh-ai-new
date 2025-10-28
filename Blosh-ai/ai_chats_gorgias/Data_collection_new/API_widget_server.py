"""
Gorgias Widget API Server
Flask server that provides AI response suggestions for Gorgias tickets
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import logging
from datetime import datetime
from improved_response_generator import generate_response
import base64
import requests

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')

# Set OpenAI key for response generator
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple cache for suggestions (in production, use Redis)
suggestions_cache = {}

# ============================================================================
# GORGIAS API HELPERS
# ============================================================================

def get_gorgias_headers():
    """Get headers for Gorgias API requests"""
    return {
        'accept': 'application/json',
        'authorization': GORGIAS_AUTH,
        'content-type': 'application/json'
    }

def get_ticket_data(ticket_id):
    """Fetch ticket data from Gorgias API"""
    try:
        url = f"{GORGIAS_BASE_URL}/tickets/{ticket_id}"
        response = requests.get(url, headers=get_gorgias_headers(), timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch ticket {ticket_id}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching ticket: {str(e)}")
        return None

def get_ticket_messages(ticket_id):
    """Fetch ticket messages from Gorgias API"""
    try:
        url = f"{GORGIAS_BASE_URL}/tickets/{ticket_id}/messages"
        response = requests.get(url, headers=get_gorgias_headers(), timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch messages for ticket {ticket_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return None

def extract_ticket_info(ticket_data):
    """Extract relevant info from Gorgias ticket data"""
    if not ticket_data:
        return None
    
    # Get customer info
    customer = ticket_data.get('customer', {})
    customer_name = customer.get('firstname', '') or customer.get('name', '').split()[0] if customer.get('name') else ''
    
    # Get last message from messages endpoint or from ticket data
    last_customer_message = ''
    messages = ticket_data.get('messages', [])
    
    if messages:
        for msg in reversed(messages):
            if msg.get('source', {}).get('type') == 'customer':
                last_customer_message = msg.get('body_text', '')
                break
    
    # Fallback: try to get from ticket's last_message
    if not last_customer_message and 'last_message' in ticket_data:
        last_customer_message = ticket_data.get('last_message', {}).get('body_text', '')
    
    # Try to extract order number from tags or subject
    tags = ticket_data.get('tags', [])
    order_number = None
    
    for tag in tags:
        if isinstance(tag, dict):
            tag_name = tag.get('name', '')
        else:
            tag_name = str(tag)
        
        # Look for order numbers in tags
        if tag_name.startswith('102') or tag_name.startswith('203'):
            order_number = tag_name
            break
    
    # Also try to find order number in subject
    if not order_number:
        subject = ticket_data.get('subject', '')
        import re
        order_match = re.search(r'\b(102\d{6}|203\d{5})\b', subject)
        if order_match:
            order_number = order_match.group(1)
    
    return {
        'ticket_id': ticket_data.get('id'),
        'customer_name': customer_name,
        'customer_email': customer.get('email', ''),
        'subject': ticket_data.get('subject', ''),
        'message': last_customer_message,
        'order_number': order_number,
        'channel': ticket_data.get('channel', 'email')
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/suggest', methods=['POST'])
def suggest_response():
    """
    Generate AI suggestion for a ticket
    
    Expects JSON:
    {
        "ticket_id": "123456",
        "customer_name": "Petra",
        "message": "Ik wil retour doen",
        "order_number": "102345678",
        "subject": "Retour"
    }
    """
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        
        if not ticket_id:
            return jsonify({'error': 'ticket_id required'}), 400
        
        logger.info(f"Generating suggestion for ticket {ticket_id}")
        
        # Check cache first
        if ticket_id in suggestions_cache:
            logger.info(f"Returning cached suggestion for {ticket_id}")
            cached = suggestions_cache[ticket_id]
            cached['cached'] = True
            return jsonify(cached)
        
        # Extract info
        customer_name = data.get('customer_name', '')
        message = data.get('message', '')
        order_number = data.get('order_number', '')
        subject = data.get('subject', '')
        
        # If message is empty, try to fetch from Gorgias
        if not message:
            ticket_data = get_ticket_data(ticket_id)
            if ticket_data:
                info = extract_ticket_info(ticket_data)
                if info:
                    customer_name = info['customer_name']
                    message = info['message']
                    order_number = info['order_number'] or order_number
                    subject = info['subject']
        
        if not message:
            return jsonify({'error': 'No message found'}), 400
        
        # Generate AI response
        result = generate_response(
            customer_message=message,
            customer_name=customer_name,
            order_number=order_number,
            subject=subject
        )
        
        if not result:
            return jsonify({'error': 'Failed to generate response'}), 500
        
        # Prepare response
        response_data = {
            'ticket_id': ticket_id,
            'suggestion': result['response'],
            'quality_score': result['quality_score'],
            'confidence': result['quality_score'],
            'brand': result['brand'],
            'warnings': result.get('warnings', []),
            'approved': result['approved'],
            'timestamp': datetime.now().isoformat(),
            'cached': False
        }
        
        # Cache it
        suggestions_cache[ticket_id] = response_data
        
        logger.info(f"Generated suggestion for {ticket_id} - Quality: {result['quality_score']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in suggest_response: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """Record agent feedback on suggestions"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        feedback = data.get('feedback')  # 'used', 'edited', 'ignored'
        
        logger.info(f"Feedback for ticket {ticket_id}: {feedback}")
        
        # TODO: Store in database for analytics
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WIDGET ENDPOINT
# ============================================================================

@app.route('/widget/<ticket_id>', methods=['GET'])
def widget(ticket_id):
    """
    Gorgias sidebar widget - displays AI suggestion in an iframe
    This endpoint returns full HTML that Gorgias will render in the sidebar
    """
    
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
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e9ecef;
        }
        .header h3 {
            color: #2c3e50;
            font-size: 16px;
            flex: 1;
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
        
        .loading {
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #2196f3;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
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
            margin-bottom: 12px;
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
            max-height: 400px;
            overflow-y: auto;
        }
        
        .actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
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
            box-shadow: 0 2px 8px rgba(33,150,243,0.3);
        }
        .btn-secondary {
            background: #e9ecef;
            color: #495057;
        }
        .btn-secondary:hover {
            background: #dee2e6;
        }
        
        .info {
            display: flex;
            gap: 12px;
            margin-top: 12px;
            font-size: 12px;
            color: #6c757d;
        }
        .info-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin: 12px 0;
            font-size: 12px;
            color: #856404;
            border-radius: 4px;
        }
        .warning-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .error {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 12px;
            color: #721c24;
            border-radius: 4px;
        }
        
        .feedback {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e9ecef;
            text-align: center;
        }
        .feedback-label {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 8px;
        }
        .feedback-btns {
            display: flex;
            gap: 6px;
            justify-content: center;
        }
        .feedback-btn {
            padding: 6px 12px;
            font-size: 12px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .feedback-btn:hover {
            background: #e9ecef;
        }
        .feedback-btn.active {
            background: #2196f3;
            color: white;
            border-color: #2196f3;
        }
        
        .brand-tag {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
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
            <div>Generating suggestion...</div>
        </div>
    </div>

    <script>
        const TICKET_ID = "{{ ticket_id }}";
        const API_URL = window.location.origin;
        
        let currentSuggestion = null;
        
        async function loadSuggestion() {
            try {
                // First, try to fetch from cache or generate new suggestion
                const response = await fetch(`${API_URL}/api/suggest`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ticket_id: TICKET_ID
                    })
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentSuggestion = data;
                displaySuggestion(data);
                
            } catch (error) {
                console.error('Error loading suggestion:', error);
                displayError(error.message || 'Failed to load suggestion');
            }
        }
        
        function displaySuggestion(data) {
            const qualityScore = data.quality_score || data.confidence || 0;
            const confidenceBadge = qualityScore >= 70 ? 'badge-high' : qualityScore >= 50 ? 'badge-medium' : 'badge-low';
            const confidenceText = qualityScore >= 70 ? 'High' : qualityScore >= 50 ? 'Medium' : 'Low';
            
            const warnings = data.warnings || [];
            const warningHtml = warnings.length > 0 ? `
                <div class="warning">
                    <div class="warning-title">⚠️ Review Needed:</div>
                    ${warnings.map(w => `<div>• ${w}</div>`).join('')}
                </div>
            ` : '';
            
            document.getElementById('content').innerHTML = `
                <div class="suggestion-box">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="brand-tag">${data.brand || 'Freebird Icons'}</span>
                        <span class="badge ${confidenceBadge}">${confidenceText} Quality (${qualityScore}%)</span>
                    </div>
                    
                    ${warningHtml}
                    
                    <div class="suggestion-text">${escapeHtml(data.suggestion)}</div>
                    
                    <div class="actions">
                        <button class="btn btn-primary" onclick="useSuggestion()">
                            ✓ Use Response
                        </button>
                        <button class="btn btn-secondary" onclick="copySuggestion()">
                            📋 Copy
                        </button>
                    </div>
                    
                    <div class="info">
                        <div class="info-item">
                            <span>🎯</span>
                            <span>Ticket #${TICKET_ID}</span>
                        </div>
                        ${data.cached ? '<div class="info-item"><span>💾</span><span>Cached</span></div>' : ''}
                    </div>
                </div>
                
                <div class="feedback">
                    <div class="feedback-label">Was this helpful?</div>
                    <div class="feedback-btns">
                        <button class="feedback-btn" onclick="sendFeedback('used')">👍 Used It</button>
                        <button class="feedback-btn" onclick="sendFeedback('edited')">✏️ Edited</button>
                        <button class="feedback-btn" onclick="sendFeedback('ignored')">👎 Ignored</button>
                    </div>
                </div>
            `;
        }
        
        function displayError(message) {
            document.getElementById('content').innerHTML = `
                <div class="error">
                    <strong>Error:</strong> ${escapeHtml(message)}
                    <br><br>
                    <button class="btn btn-secondary" onclick="loadSuggestion()">Try Again</button>
                </div>
            `;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function useSuggestion() {
            if (!currentSuggestion) return;
            
            // Copy to clipboard
            await navigator.clipboard.writeText(currentSuggestion.suggestion);
            
            // Visual feedback
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '✓ Copied!';
            btn.style.background = '#4caf50';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.background = '';
            }, 2000);
            
            // Record feedback
            sendFeedback('used');
            
            alert('Response copied to clipboard! Paste it into your reply field.');
        }
        
        async function copySuggestion() {
            if (!currentSuggestion) return;
            
            await navigator.clipboard.writeText(currentSuggestion.suggestion);
            
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '✓ Copied';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
            }, 2000);
        }
        
        async function sendFeedback(type) {
            try {
                await fetch(`${API_URL}/api/feedback`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        ticket_id: TICKET_ID,
                        feedback: type
                    })
                });
                
                // Visual feedback
                document.querySelectorAll('.feedback-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
            } catch (error) {
                console.error('Error sending feedback:', error);
            }
        }
        
        // Auto-load on page load
        window.addEventListener('load', loadSuggestion);
    </script>
</body>
</html>
    """
    
    return render_template_string(widget_html, ticket_id=ticket_id)

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Gorgias AI Widget Server")
    logger.info("="*60)
    logger.info(f"OpenAI API Key: {'✓ Set' if OPENAI_API_KEY else '✗ Not Set'}")
    logger.info(f"Gorgias Auth: {'✓ Set' if GORGIAS_AUTH else '✗ Not Set'}")
    logger.info(f"Gorgias URL: {GORGIAS_BASE_URL}")
    logger.info("="*60)
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health                  - Health check")
    logger.info("  POST /api/suggest             - Generate AI suggestion")
    logger.info("  POST /api/feedback            - Record feedback")
    logger.info("  GET  /widget/<ticket_id>      - Widget interface")
    logger.info("")
    logger.info("="*60)
    
    # Run server
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_ENV') == 'development'
    )

