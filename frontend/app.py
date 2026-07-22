import os
from datetime import datetime

import requests
from api_client import BackendAPIClient
from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

# Configuration
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8081')
RECORDING_APP_URL = os.getenv('RECORDING_APP_URL', 'http://localhost:5000')
api_client = BackendAPIClient(BACKEND_API_URL)

@app.route('/')
def index():
    """Main page - recording interface"""
    return render_template('record.html',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page displaying latest recording"""
    # Fetch latest recording
    recordings_data = api_client.get_recordings()

    # Get the most recent recording if available
    latest_recording = None
    if recordings_data and 'recordings' in recordings_data and recordings_data['recordings']:
        latest_recording = recordings_data['recordings'][0]
        # Get additional data for the latest recording
        recording_id = latest_recording['id']
        transcript = api_client.get_transcript(recording_id)
        summary = api_client.get_summary(recording_id)

        latest_recording['transcript'] = transcript
        latest_recording['summary'] = summary

    return render_template('index.html',
                         transcription=latest_recording,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/history')
def history():
    """History page with previous recordings"""
    recordings_data = api_client.get_recordings()

    # Enhance recordings with status and additional info
    if recordings_data and 'recordings' in recordings_data:
        for recording in recordings_data['recordings']:
            recording_id = recording['id']
            status = api_client.get_recording_status(recording_id)
            if status:
                recording['processing_status'] = status.get('status')
                recording['error'] = status.get('error') if status.get('status') == 'failed' else None

    return render_template('history.html',
                         history=recordings_data,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/participants')
def participants():
    """Participants list page - derived from transcript speakers"""
    # Get latest recording to extract participants
    recordings_data = api_client.get_recordings()
    participants = []

    if recordings_data and 'recordings' in recordings_data and recordings_data['recordings']:
        latest_recording = recordings_data['recordings'][0]
        recording_id = latest_recording['id']
        transcript = api_client.get_transcript(recording_id)

        if transcript and 'segments' in transcript:
            # Extract unique speakers from transcript
            speakers = set()
            for segment in transcript['segments']:
                if 'speaker' in segment:
                    speakers.add(segment['speaker'])

            # Create participant list
            for speaker in speakers:
                participants.append({
                    'name': speaker,
                    'role': 'Speaker',
                    'meeting_count': 1,
                    'last_meeting': latest_recording.get('recordedAt', 'Unknown'),
                    'active': True
                })

    return render_template('participants.html',
                         participants=participants,
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

@app.route('/recording/<recording_id>')
def recording_detail(recording_id):
    """Recording detail page"""
    # Get recording metadata
    recordings_data = api_client.get_recordings()
    recording = None

    if recordings_data and 'recordings' in recordings_data:
        for rec in recordings_data['recordings']:
            if rec['id'] == recording_id:
                recording = rec
                break

    if recording:
        # Get additional data
        transcript = api_client.get_transcript(recording_id)
        summary = api_client.get_summary(recording_id)
        analysis = api_client.get_analysis(recording_id)
        status = api_client.get_recording_status(recording_id)

        recording['transcript'] = transcript
        recording['summary'] = summary
        recording['analysis'] = analysis
        recording['status'] = status.get('status') if status else 'unknown'

    return render_template('recording_detail.html',
                         recording=recording,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/status')
def proxy_status():
    """Proxy to recording app status endpoint"""
    try:
        response = requests.get(f"{RECORDING_APP_URL}/api/status", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

@app.route('/api/record/start', methods=['POST'])
def proxy_record_start():
    """Proxy to recording app start endpoint"""
    try:
        response = requests.post(f"{RECORDING_APP_URL}/api/record/start", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

@app.route('/api/record/stop', methods=['POST'])
def proxy_record_stop():
    """Proxy to recording app stop endpoint"""
    try:
        response = requests.post(f"{RECORDING_APP_URL}/api/record/stop", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

@app.route('/api/record/send', methods=['POST'])
def proxy_record_send():
    """Proxy to recording app send endpoint"""
    try:
        response = requests.post(f"{RECORDING_APP_URL}/api/record/send", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

@app.route('/api/recording/file')
def proxy_recording_file():
    """Proxy to recording app file endpoint"""
    try:
        response = requests.get(f"{RECORDING_APP_URL}/api/recording/file", params=request.args, stream=True)
        return send_file_response(response)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

def send_file_response(response):
    """Helper to stream file response from recording app"""
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    headers = dict(response.headers)
    return generate(), response.status_code, headers

@app.route('/api/recordings/<recording_id>/status')
def get_recording_status(recording_id):
    """Get processing status for a recording"""
    status = api_client.get_recording_status(recording_id)
    return jsonify(status)

@app.route('/api/recordings/<recording_id>/transcript')
def get_recording_transcript(recording_id):
    """Get transcript for a recording"""
    transcript = api_client.get_transcript(recording_id)
    return jsonify(transcript)

@app.route('/api/recordings/<recording_id>/summary')
def get_recording_summary(recording_id):
    """Get summary for a recording"""
    summary = api_client.get_summary(recording_id)
    return jsonify(summary)

@app.route('/api/recordings/<recording_id>/analysis')
def get_recording_analysis(recording_id):
    """Get analysis for a recording"""
    analysis = api_client.get_analysis(recording_id)
    return jsonify(analysis)

@app.route('/api/refresh')
def refresh_data():
    """Force refresh of current data"""
    recordings_data = api_client.get_recordings()
    return jsonify(recordings_data)

@app.route('/temp/<path:filename>')
def serve_temp(filename):
    """Serve files from temp directory"""
    return send_from_directory('temp', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
