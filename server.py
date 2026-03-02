"""
Web server for triggering scheduled reports via HTTP.
Can be called by external cron services (EasyCron, cron-job.org, etc.)
"""

from flask import Flask, request, jsonify
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import MovideskAutomation

app = Flask(__name__)

# Security token (configure in environment)
TRIGGER_TOKEN = os.getenv('TRIGGER_TOKEN', 'change-me-in-production')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'movidesk-automation'
    }), 200

@app.route('/trigger', methods=['POST'])
def trigger_reports():
    """Trigger daily reports for all agents"""
    # Verify security token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token != TRIGGER_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Run scheduled report
        automation = MovideskAutomation(
            mode='scheduled-report',
            run_once=True
        )
        
        automation.run()
        
        return jsonify({
            'status': 'success',
            'message': 'Reports sent to all agents'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
