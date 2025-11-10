"""
Gorgias Widget API Server v2.0
Flask server with persistent database and automatic suggestion generation
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
import threading
from datetime import datetime
from improved_response_generator import generate_response
from database import get_db
from ticket_sync import get_sync
from suggestion_manager import get_manager

# Initialize Flask
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://*.gorgias.com", "https://freebirdicons.gorgias.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GORGIAS_AUTH = os.getenv('GORGIAS_AUTH')
GORGIAS_BASE_URL = os.getenv('GORGIAS_BASE_URL', 'https://freebirdicons.gorgias.com/api')

# Set OpenAI key for response generator
if OPENAI_API_KEY:
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
db = get_db()
sync = get_sync()
manager = get_manager()

# Background scheduler for periodic tasks
scheduler = BackgroundScheduler()
initialization_done = False

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_system():
    """Initialize the system on startup"""
    global initialization_done
    
    if initialization_done:
        logger.info("System already initialized")
        return
    
    logger.info("="*60)
    logger.info("🚀 INITIALIZING SYSTEM")
    logger.info("="*60)
    
    try:
        # Step 1: Check database
        ticket_count = db.get_ticket_count()
        logger.info(f"Database has {ticket_count} tickets")
        
        # Step 2: Sync recent tickets if database is empty or small
        if ticket_count < 10:
            logger.info("Database has fewer than 10 tickets, syncing from Gorgias...")
            synced = sync.sync_recent_tickets(limit=100)
            logger.info(f"Synced {synced} tickets from Gorgias")
        else:
            logger.info("Syncing latest 20 tickets to catch any new ones...")
            synced = sync.sync_recent_tickets(limit=20)
            logger.info(f"Synced {synced} tickets")
        
        # Step 3: Ensure top 10 have suggestions
        logger.info("Ensuring top 10 tickets have suggestions...")
        result = manager.ensure_suggestions_for_top_n()
        logger.info(f"Suggestion status: {result}")
        
        # Step 4: Show stats
        stats = db.get_stats()
        logger.info("="*60)
        logger.info("📊 SYSTEM STATISTICS")
        logger.info("="*60)
        logger.info(f"Total tickets: {stats.get('total_tickets', 0)}")
        logger.info(f"Tickets with suggestions: {stats.get('tickets_with_suggestions', 0)}")
        logger.info(f"Recent tickets (top 10): {stats.get('recent_tickets_count', 0)}")
        logger.info(f"Recent with suggestions: {stats.get('recent_tickets_with_suggestions', 0)}")
        logger.info(f"Coverage: {stats.get('coverage_percentage', 0):.1f}%")
        logger.info("="*60)
        
        initialization_done = True
        logger.info("✅ System initialization complete")
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}", exc_info=True)

def periodic_sync():
    """Periodic task to sync new tickets and maintain suggestions"""
    try:
        logger.info("Running periodic sync...")
        
        # Sync recent tickets
        synced = sync.sync_recent_tickets(limit=20)
        logger.info(f"Periodic sync: {synced} tickets synced")
        
        # Ensure top 10 have suggestions
        result = manager.ensure_suggestions_for_top_n()
        logger.info(f"Periodic sync: {result}")
        
    except Exception as e:
        logger.error(f"Error in periodic sync: {e}", exc_info=True)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    stats = db.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'service': 'Gorgias AI Widget API',
        'version': '2.0',
        'database': {
            'total_tickets': stats.get('total_tickets', 0),
            'tickets_with_suggestions': stats.get('tickets_with_suggestions', 0),
            'coverage': f"{stats.get('coverage_percentage', 0):.1f}%"
        },
        'endpoints': {
            'health': '/health',
            'stats': '/api/stats',
            'suggest_post': 'POST /api/suggest - Generate suggestion',
            'suggest_get': 'GET /api/suggest/<ticket_id> - Get suggestion',
            'widget': '/widget/<ticket_id>',
            'sync': 'POST /api/sync - Trigger sync',
            'init': 'POST /api/init - Trigger initialization'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    stats = db.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'initialized': initialization_done,
        'database': stats
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get detailed statistics"""
    stats = db.get_stats()
    top_tickets = manager.get_top_n_tickets()
    
    return jsonify({
        'database': stats,
        'top_tickets': [
            {
                'ticket_id': t['ticket_id'],
                'created_at': t['created_at'],
                'subject': t['subject'][:50] if t.get('subject') else '',
                'has_suggestion': db.has_suggestion(t['ticket_id'])
            }
            for t in top_tickets
        ]
    })

@app.route('/api/init', methods=['POST'])
def trigger_init():
    """Manually trigger initialization"""
    global initialization_done
    initialization_done = False
    
    thread = threading.Thread(target=initialize_system, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'initialization_started',
        'message': 'System initialization triggered in background'
    })

@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """Manually trigger ticket sync"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 20)
        
        # Run sync in background
        def do_sync():
            synced = sync.sync_recent_tickets(limit=limit)
            result = manager.ensure_suggestions_for_top_n()
            logger.info(f"Manual sync complete: {synced} tickets, {result}")
        
        thread = threading.Thread(target=do_sync, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'sync_started',
            'message': f'Syncing {limit} tickets in background'
        })
        
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/suggest/<ticket_id>', methods=['GET'])
def get_suggestion(ticket_id):
    """Get suggestion for a ticket"""
    try:
        logger.info(f"GET request for suggestion {ticket_id}")
        
        # Check database first
        suggestion = db.get_suggestion(ticket_id)
        
        if suggestion:
            logger.info(f"✅ Returning suggestion for {ticket_id}")
            return jsonify({
                'ticket_id': ticket_id,
                'suggestion': suggestion['suggestion_text'],
                'quality_score': suggestion['quality_score'],
                'confidence': suggestion['confidence'],
                'brand': suggestion['brand'],
                'warnings': suggestion['warnings'],
                'approved': suggestion['approved'],
                'timestamp': suggestion['generated_at'],
                'cached': True
            })
        else:
            logger.info(f"❌ No suggestion found for {ticket_id}")
            return jsonify({
                'status': 'not_ready',
                'ticket_id': ticket_id,
                'message': 'Suggestion not ready yet'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting suggestion: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/suggest', methods=['POST'])
def generate_suggestion():
    """Generate a suggestion for a ticket"""
    try:
        raw_data = request.get_json()
        
        # Handle Gorgias form array format
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and isinstance(raw_data[0], dict):
                if 'key' in raw_data[0] and 'value' in raw_data[0]:
                    data = {item['key']: item['value'] for item in raw_data}
                else:
                    data = raw_data[0]
            else:
                return jsonify({'error': 'Invalid data format'}), 400
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            return jsonify({'error': f'Invalid data type: {type(raw_data)}'}), 400
        
        ticket_id = data.get('ticket_id')
        if not ticket_id:
            return jsonify({'error': 'ticket_id required'}), 400
        
        logger.info(f"Generate request for ticket {ticket_id}")
        
        # Check if suggestion already exists
        existing = db.get_suggestion(ticket_id)
        if existing:
            logger.info(f"Returning existing suggestion for {ticket_id}")
            return jsonify({
                'ticket_id': ticket_id,
                'suggestion': existing['suggestion_text'],
                'quality_score': existing['quality_score'],
                'confidence': existing['confidence'],
                'brand': existing['brand'],
                'warnings': existing['warnings'],
                'approved': existing['approved'],
                'timestamp': existing['generated_at'],
                'cached': True
            })
        
        # Start background generation
        def generate_in_background():
            try:
                logger.info(f"Background: Generating for ticket {ticket_id}")
                
                # First, ensure ticket is in database
                ticket = db.get_ticket(ticket_id)
                if not ticket:
                    logger.info(f"Ticket {ticket_id} not in DB, syncing from Gorgias...")
                    sync.sync_ticket(ticket_id)
                    ticket = db.get_ticket(ticket_id)
                
                if not ticket:
                    logger.error(f"Failed to sync ticket {ticket_id}")
                    return
                
                # Generate suggestion
                manager.generate_suggestion_for_ticket(ticket)
                logger.info(f"Background: ✅ Generated suggestion for {ticket_id}")
                
            except Exception as e:
                logger.error(f"Background: ❌ Error generating for {ticket_id}: {e}", exc_info=True)
        
        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'accepted',
            'ticket_id': ticket_id,
            'message': 'Generation started',
            'timestamp': datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error in generate_suggestion: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """Record agent feedback on suggestions"""
    try:
        raw_data = request.get_json()
        
        # Handle Gorgias form array format
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and isinstance(raw_data[0], dict):
                if 'key' in raw_data[0] and 'value' in raw_data[0]:
                    data = {item['key']: item['value'] for item in raw_data}
                else:
                    data = raw_data[0]
            else:
                return jsonify({'error': 'Invalid data format'}), 400
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            return jsonify({'error': f'Invalid data type: {type(raw_data)}'}), 400
        
        ticket_id = data.get('ticket_id')
        feedback = data.get('feedback')
        
        logger.info(f"Feedback for ticket {ticket_id}: {feedback}")
        
        # TODO: Store feedback in database for analytics
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WIDGET ENDPOINT
# ============================================================================

@app.route('/widget/<ticket_id>', methods=['GET', 'POST'])
def widget(ticket_id):
    """Gorgias sidebar widget"""
    
    if request.method == 'POST':
        # Handle POST from HTTP integration
        logger.info(f"POST request to widget for ticket {ticket_id}")
        
        try:
            # Ensure ticket is synced and has suggestion
            ticket = db.get_ticket(ticket_id)
            if not ticket:
                sync.sync_ticket(ticket_id)
            
            # Queue for suggestion generation if needed
            if not db.has_suggestion(ticket_id):
                manager.generate_suggestion_async(ticket_id)
            
            return jsonify({
                'status': 'success',
                'ticket_id': ticket_id,
                'message': 'Widget triggered',
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"Error processing POST to widget: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # GET request - return widget HTML
    logger.info(f"GET request to widget for ticket {ticket_id}")
    
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
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
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
        
        .no-suggestion {
            text-align: center;
            padding: 40px 20px;
        }
        .no-suggestion .icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .no-suggestion .message {
            color: #6c757d;
            margin-bottom: 16px;
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

    <script>
        const TICKET_ID = "{{ ticket_id }}";
        const API_URL = window.location.origin;
        
        let currentSuggestion = null;
        let isGenerating = false;
        
        async function loadSuggestion() {
            try {
                console.log(`Loading suggestion for ticket ${TICKET_ID}...`);
                
                // Try to get existing suggestion
                let response = await fetch(`${API_URL}/api/suggest/${TICKET_ID}`, {
                    method: 'GET'
                });
                
                console.log(`Response status: ${response.status}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Received data:', data);
                    displaySuggestion(data);
                } else if (response.status === 404) {
                    // No suggestion exists yet
                    displayNoSuggestion();
                } else {
                    throw new Error(`Failed to load suggestion: ${response.status}`);
                }
                
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
            
            if (isGenerating) return;
            
            isGenerating = true;
            
            try {
                // Show loading state
                document.getElementById('content').innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <div>Generating AI suggestion...</div>
                        <div style="font-size: 12px; color: #6c757d; margin-top: 8px;">
                            This takes 5-10 seconds
                        </div>
                    </div>
                `;
                
                // Trigger generation
                await fetch(`${API_URL}/api/suggest`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ticket_id: TICKET_ID})
                });
                
                // Poll for result
                let attempts = 0;
                const maxAttempts = 15;
                
                while (attempts < maxAttempts) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    attempts++;
                    
                    console.log(`Polling attempt ${attempts}/${maxAttempts}...`);
                    
                    document.getElementById('content').innerHTML = `
                        <div class="loading">
                            <div class="spinner"></div>
                            <div>Generating AI suggestion...</div>
                            <div style="font-size: 12px; color: #6c757d; margin-top: 8px;">
                                ${attempts * 2}s / ${maxAttempts * 2}s
                            </div>
                        </div>
                    `;
                    
                    const response = await fetch(`${API_URL}/api/suggest/${TICKET_ID}`);
                    
                    if (response.ok) {
                        const data = await response.json();
                        displaySuggestion(data);
                        return;
                    }
                }
                
                throw new Error('Generation timed out. Please refresh the page.');
                
            } catch (error) {
                console.error('Error generating suggestion:', error);
                displayError(error.message || 'Failed to generate suggestion');
            } finally {
                isGenerating = false;
            }
        }
        
        function displayNoSuggestion() {
            document.getElementById('content').innerHTML = `
                <div class="no-suggestion">
                    <div class="icon">💡</div>
                    <div class="message">No AI suggestion yet for this ticket</div>
                    <button type="button" class="btn btn-primary" onclick="generateSuggestion(event)">
                        Generate Response
                    </button>
                </div>
            `;
        }
        
        function displaySuggestion(data) {
            if (!data || !data.suggestion) {
                displayError('No suggestion available');
                return;
            }
            
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
                        <button type="button" class="btn btn-primary" onclick="useSuggestion(event)">
                            ✓ Use Response
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="copySuggestion(event)">
                            📋 Copy
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="generateSuggestion(event)">
                            🔄 Regenerate
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
                            <button type="button" class="feedback-btn" data-feedback="used" onclick="sendFeedback('used', event)">👍 Used It</button>
                            <button type="button" class="feedback-btn" data-feedback="edited" onclick="sendFeedback('edited', event)">✏️ Edited</button>
                            <button type="button" class="feedback-btn" data-feedback="ignored" onclick="sendFeedback('ignored', event)">👎 Ignored</button>
                    </div>
                </div>
            `;
            
            currentSuggestion = data;
        }
        
        function displayError(message) {
            document.getElementById('content').innerHTML = `
                <div class="error">
                    <strong>Error:</strong> ${escapeHtml(message)}
                    <br><br>
                    <button type="button" class="btn btn-secondary" onclick="loadSuggestion()">Try Again</button>
                </div>
            `;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function useSuggestion(evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }
            
            if (!currentSuggestion) return;
            
            await navigator.clipboard.writeText(currentSuggestion.suggestion);
            
            const btn = evt ? (evt.currentTarget || evt.target) : null;
            const originalText = btn ? btn.innerHTML : null;
            if (btn) {
                btn.innerHTML = '✓ Copied!';
                btn.style.background = '#4caf50';
            }
            
            setTimeout(() => {
                if (btn && originalText !== null) {
                    btn.innerHTML = originalText;
                    btn.style.background = '';
                }
            }, 2000);
            
            sendFeedback('used');
            
            alert('Response copied to clipboard! Paste it into your reply field.');
        }
        
        async function copySuggestion(evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }
            
            if (!currentSuggestion) return;
            
            await navigator.clipboard.writeText(currentSuggestion.suggestion);
            
            const btn = evt ? (evt.currentTarget || evt.target) : null;
            const originalText = btn ? btn.innerHTML : null;
            if (btn) {
                btn.innerHTML = '✓ Copied';
            }
            
            setTimeout(() => {
                if (btn && originalText !== null) {
                    btn.innerHTML = originalText;
                }
            }, 2000);
        }
        
        async function sendFeedback(type, evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }
            
            try {
                await fetch(`${API_URL}/api/feedback`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        ticket_id: TICKET_ID,
                        feedback: type
                    })
                });
                
                const buttons = document.querySelectorAll('.feedback-btn');
                buttons.forEach(btn => {
                    btn.classList.remove('active');
                });
                
                const targetButton = evt
                    ? (evt.currentTarget || evt.target)
                    : document.querySelector(`.feedback-btn[data-feedback="${type}"]`);
                
                if (targetButton) {
                    targetButton.classList.add('active');
                }
                
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
# STARTUP
# ============================================================================

def startup():
    """Run startup tasks"""
    logger.info("="*60)
    logger.info("🚀 Gorgias AI Widget Server v2.0 Starting")
    logger.info("="*60)
    logger.info(f"OpenAI API Key: {'✓ Set' if OPENAI_API_KEY else '✗ Not Set'}")
    logger.info(f"Gorgias Auth: {'✓ Set' if GORGIAS_AUTH else '✗ Not Set'}")
    logger.info(f"Gorgias URL: {GORGIAS_BASE_URL}")
    logger.info("="*60)
    
    # Initialize system in background
    thread = threading.Thread(target=initialize_system, daemon=True)
    thread.start()
    
    # Start periodic sync (every 5 minutes)
    if not scheduler.running:
        scheduler.add_job(periodic_sync, 'interval', minutes=5, id='periodic_sync')
        scheduler.start()
        logger.info("✅ Periodic sync scheduled (every 5 minutes)")

# Run startup when module is imported
startup()

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Running in development mode on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )

