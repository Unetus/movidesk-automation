"""
Web server for triggering scheduled reports via HTTP.
Can be called by external cron services (EasyCron, cron-job.org, etc.)
"""

from flask import Flask, request, jsonify
import os
import sys
import subprocess

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
        # Run scheduled report via subprocess
        result = subprocess.run(
            [sys.executable, 'main.py', '--scheduled-report'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Reports sent to all agents',
                'output': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send reports',
                'error': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
            }), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Report generation timed out (>10 minutes)'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
