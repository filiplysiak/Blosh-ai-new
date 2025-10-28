"""
API Helper functions for Brand Analyzer
"""

import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from .analyzer import BrandAnalyzer


# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'input_files')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'output_files')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'template_blosh.docx')
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, week_number, year):
    """Save uploaded PDF file"""
    try:
        if not file or not allowed_file(file.filename):
            return False, "Invalid file type. Only PDF files are allowed."
        
        filename = secure_filename(file.filename)
        week_dir = f"week_{week_number}_{year}"
        upload_dir = os.path.join(UPLOAD_FOLDER, week_dir)
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        return True, filepath
    except Exception as e:
        return False, f"Error saving file: {str(e)}"


def process_pdf(filepath, week_number, year):
    """Process PDF and generate analysis"""
    try:
        analyzer = BrandAnalyzer(filepath, TEMPLATE_PATH, OUTPUT_FOLDER)
        
        # Extract tables
        success, message = analyzer.extract_tables()
        if not success:
            return False, message
        
        # Generate analysis
        success, result = analyzer.generate_analysis(week_number, year)
        if not success:
            return False, result
        
        return True, result
    except Exception as e:
        return False, f"Error processing PDF: {str(e)}"


def get_all_analyses():
    """Get list of all analyses"""
    try:
        analyses = []
        
        if not os.path.exists(OUTPUT_FOLDER):
            return []
        
        for week_dir in os.listdir(OUTPUT_FOLDER):
            week_path = os.path.join(OUTPUT_FOLDER, week_dir)
            if not os.path.isdir(week_path):
                continue
            
            metadata_path = os.path.join(week_path, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    summary = metadata.get('summary', {})
                    # Include files in summary for easy access
                    summary['files'] = metadata.get('files', {})
                    analyses.append({
                        'id': week_dir,
                        'week_number': metadata.get('week_number'),
                        'year': metadata.get('year'),
                        'upload_date': metadata.get('upload_date'),
                        'status': metadata.get('status'),
                        'summary': summary,
                        'brands_data': summary.get('competitors', {}),
                        'group_average': summary.get('group_average', {})
                    })
        
        # Sort by week number (newest first)
        analyses.sort(key=lambda x: (x.get('year', 0), x.get('week_number', 0)), reverse=True)
        return analyses
    except Exception as e:
        print(f"Error getting analyses: {str(e)}")
        return []


def get_analysis_detail(analysis_id):
    """Get detailed analysis data"""
    try:
        analysis_path = os.path.join(OUTPUT_FOLDER, analysis_id)
        metadata_path = os.path.join(analysis_path, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return None, "Analysis not found"
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return metadata, None
    except Exception as e:
        return None, f"Error getting analysis: {str(e)}"


def get_file_path(analysis_id, file_type):
    """Get path to a specific file"""
    try:
        analysis_path = os.path.join(OUTPUT_FOLDER, analysis_id)
        metadata_path = os.path.join(analysis_path, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return None, "Analysis not found"
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        files = metadata.get('files', {})
        filename = files.get(file_type)
        
        if not filename:
            return None, f"File type '{file_type}' not found"
        
        filepath = os.path.join(analysis_path, filename)
        
        if not os.path.exists(filepath):
            return None, "File not found on disk"
        
        return filepath, None
    except Exception as e:
        return None, f"Error getting file: {str(e)}"


def delete_analysis(analysis_id):
    """Delete an analysis and all its files"""
    try:
        import shutil
        
        # Delete from output folder
        output_path = os.path.join(OUTPUT_FOLDER, analysis_id)
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        
        # Delete from input folder
        input_path = os.path.join(UPLOAD_FOLDER, analysis_id)
        if os.path.exists(input_path):
            shutil.rmtree(input_path)
        
        return True, "Analysis deleted successfully"
    except Exception as e:
        return False, f"Error deleting analysis: {str(e)}"


