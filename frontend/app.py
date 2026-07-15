import os
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)

# Configuration
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')

def get_backend_data(endpoint):
    """Fetch data from the backend API"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from backend: {e}")
        return None

@app.route('/')
def index():
    """Main page displaying current transcription"""
    # Fetch current transcription data
    transcription_data = get_backend_data('transcription/current')

    return render_template('index.html',
                         transcription=transcription_data,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/history')
def history():
    """History page with previous recordings"""
    history_data = get_backend_data('transcription/history')

    return render_template('history.html',
                         history=history_data,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/participants')
def participants():
    """Participants list page"""
    participants_data = get_backend_data('participants')

    return render_template('participants.html',
                         participants=participants_data,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/record')
def record():
    """Recording page"""
    return render_template('record.html',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/transcription/<recording_id>')
def get_transcription(recording_id):
    """API endpoint to get specific transcription"""
    data = get_backend_data(f'transcription/{recording_id}')
    return jsonify(data)

@app.route('/api/refresh')
def refresh_data():
    """Force refresh of current data"""
    transcription_data = get_backend_data('transcription/current')
    return jsonify(transcription_data)

@app.route('/temp/<path:filename>')
def serve_temp(filename):
    """Serve files from temp directory"""
    return send_from_directory('temp', filename)

@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    """Mockup API endpoint to start recording (will later invoke Raspberry Pi function)"""
    # TODO: This will later call the Raspberry Pi recording function
    print("Starting recording (mockup - will invoke Raspberry Pi function)")
    return jsonify({
        "status": "success",
        "message": "Recording started",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    """Mockup API endpoint to stop recording (will later invoke Raspberry Pi function)"""
    # TODO: This will later call the Raspberry Pi recording function
    print("Stopping recording (mockup - will invoke Raspberry Pi function)")
    return jsonify({
        "status": "success",
        "message": "Recording stopped",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
