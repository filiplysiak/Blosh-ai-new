from flask import Flask, request, jsonify, session, send_from_directory
from datetime import timedelta
import os
import sys
import json

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from brand_analyzer import analyzer_api

# Settings file path
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'settings.json')

# Output files directory
OUTPUT_FILES_DIR = os.path.join(os.path.dirname(__file__), 'tools', 'brand_analyzer', 'output_files')

app = Flask(__name__)
app.secret_key = 'blosh-secret-key-2024'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Hardcoded password
ADMIN_PASSWORD = "Bloshai12!"

@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if password == ADMIN_PASSWORD:
            session.permanent = True
            session['authenticated'] = True
            return jsonify({
                'success': True,
                'message': 'Login successful'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid password'
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred'
        }), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    is_authenticated = session.get('authenticated', False)
    return jsonify({
        'authenticated': is_authenticated
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy'
    }), 200

# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get application settings"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        return jsonify({
            'success': True,
            'data': settings
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update application settings"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        settings = request.get_json()
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# BRAND ANALYZER ENDPOINTS
# ============================================================================

@app.route('/api/brand-analyzer/upload', methods=['POST'])
def upload_brand_analysis():
    """Upload PDF and generate analysis"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        # Check if file is present
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['pdf']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Get week number and year
        week_number = request.form.get('week_number', type=int)
        year = request.form.get('year', type=int)
        
        if not week_number or not year:
            return jsonify({'success': False, 'message': 'Week number and year are required'}), 400
        
        # Save file
        success, result = analyzer_api.save_uploaded_file(file, week_number, year)
        if not success:
            return jsonify({'success': False, 'message': result}), 400
        
        filepath = result
        
        # Process PDF
        success, result = analyzer_api.process_pdf(filepath, week_number, year)
        if not success:
            return jsonify({'success': False, 'message': result}), 500
        
        return jsonify({
            'success': True,
            'message': 'Analysis generated successfully',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/brand-analyzer/analyses', methods=['GET'])
def get_brand_analyses():
    """Get list of all analyses"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        analyses = analyzer_api.get_all_analyses()
        return jsonify({
            'success': True,
            'data': analyses
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/brand-analyzer/analysis/<analysis_id>', methods=['GET'])
def get_brand_analysis_detail(analysis_id):
    """Get detailed analysis data"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        metadata, error = analyzer_api.get_analysis_detail(analysis_id)
        if error:
            return jsonify({'success': False, 'message': error}), 404
        
        return jsonify({
            'success': True,
            'data': metadata
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/downloads/<path:filepath>')
def download_file(filepath):
    """Serve files from output directory - public endpoint"""
    try:
        return send_from_directory(OUTPUT_FILES_DIR, filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404

@app.route('/api/brand-analyzer/analysis/<analysis_id>', methods=['DELETE'])
def delete_brand_analysis(analysis_id):
    """Delete an analysis"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        success, message = analyzer_api.delete_analysis(analysis_id)
        if not success:
            return jsonify({'success': False, 'message': message}), 500
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')

