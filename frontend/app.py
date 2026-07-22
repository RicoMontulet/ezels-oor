from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from api_client import BackendAPIClient
from config import get_config

load_dotenv()

cfg = get_config()
app = Flask(__name__)
app.config.from_object(cfg)

BACKEND_API_URL = cfg.BACKEND_API_URL
RECORDING_APP_URL = cfg.RECORDING_APP_URL
api_client = BackendAPIClient(BACKEND_API_URL, timeout=cfg.BACKEND_API_TIMEOUT)


def _proxy_json(method: str, path: str, timeout: int = 5):
    try:
        response = requests.request(method, f"{RECORDING_APP_URL}{path}", timeout=timeout)
        try:
            payload = response.json()
        except ValueError:
            return jsonify({'error': 'invalid upstream response'}), 502
        return jsonify(payload), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502


def _json_or_error(result, status_code):
    if result is None:
        code = status_code if isinstance(status_code, int) and status_code >= 400 else 502
        return jsonify({'error': 'upstream request failed'}), code
    return jsonify(result)


@app.route('/')
def index():
    """Main page - recording interface"""
    return render_template('record.html',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page displaying latest recording"""
    recordings_data, _ = api_client.get_recordings()

    latest_recording = None
    if recordings_data and recordings_data.get('recordings'):
        # Backend lists newest first (recorded_at DESC).
        latest_recording = recordings_data['recordings'][0]
        recording_id = latest_recording['id']
        transcript, _ = api_client.get_transcript(recording_id)
        summary, _ = api_client.get_summary(recording_id)
        latest_recording['transcript'] = transcript
        latest_recording['summary'] = summary

    return render_template('index.html',
                         transcription=latest_recording,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/history')
def history():
    """History page with previous recordings"""
    recordings_data, _ = api_client.get_recordings()

    # Status comes from the list payload — avoid N+1 status calls.
    if recordings_data and recordings_data.get('recordings'):
        for recording in recordings_data['recordings']:
            recording['processing_status'] = recording.get('status')
            if recording.get('status') == 'failed':
                status, _ = api_client.get_recording_status(recording['id'])
                error = status.get('error') if status else None
                if isinstance(error, str):
                    recording['error'] = {'message': error}
                elif isinstance(error, dict):
                    recording['error'] = error
                else:
                    recording['error'] = None
            else:
                recording['error'] = None

    return render_template('history.html',
                         history=recordings_data,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/participants')
def participants():
    """Participants list page - derived from transcript speakers"""
    recordings_data, _ = api_client.get_recordings()
    participants_list = []

    if recordings_data and recordings_data.get('recordings'):
        latest_recording = recordings_data['recordings'][0]
        recording_id = latest_recording['id']
        transcript, _ = api_client.get_transcript(recording_id)

        if transcript and 'segments' in transcript:
            speakers = set()
            for segment in transcript['segments']:
                if 'speaker' in segment:
                    speakers.add(segment['speaker'])

            for speaker in speakers:
                participants_list.append({
                    'name': speaker,
                    'role': 'Speaker',
                    'meeting_count': 1,
                    'last_meeting': latest_recording.get('recordedAt', 'Unknown'),
                    'active': True
                })

    return render_template('participants.html',
                         participants=participants_list,
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
    recordings_data, _ = api_client.get_recordings()
    recording = None

    if recordings_data and recordings_data.get('recordings'):
        for rec in recordings_data['recordings']:
            if rec['id'] == recording_id:
                recording = rec
                break

    if recording:
        transcript, _ = api_client.get_transcript(recording_id)
        summary, _ = api_client.get_summary(recording_id)
        analysis, _ = api_client.get_analysis(recording_id)
        status, _ = api_client.get_recording_status(recording_id)

        recording['transcript'] = transcript
        recording['summary'] = summary
        recording['analysis'] = analysis
        recording['status'] = status.get('status') if status else recording.get('status', 'unknown')

    return render_template('recording_detail.html',
                         recording=recording,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/status')
def proxy_status():
    """Proxy to recording app status endpoint"""
    return _proxy_json('GET', '/api/status')

@app.route('/api/record/start', methods=['POST'])
def proxy_record_start():
    """Proxy to recording app start endpoint"""
    return _proxy_json('POST', '/api/record/start')

@app.route('/api/record/stop', methods=['POST'])
def proxy_record_stop():
    """Proxy to recording app stop endpoint"""
    return _proxy_json('POST', '/api/record/stop')

@app.route('/api/record/send', methods=['POST'])
def proxy_record_send():
    """Proxy to recording app send endpoint"""
    return _proxy_json('POST', '/api/record/send', timeout=30)

@app.route('/api/recording/file')
def proxy_recording_file():
    """Proxy to recording app file endpoint"""
    try:
        response = requests.get(
            f"{RECORDING_APP_URL}/api/recording/file",
            params=request.args,
            stream=True,
            timeout=30,
        )
        return send_file_response(response)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 502

def send_file_response(response):
    """Stream file response from recording app with safe headers only."""
    if not response.ok:
        response.close()
        return jsonify({'error': 'upstream request failed'}), response.status_code

    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    headers = {}
    content_type = response.headers.get('Content-Type')
    content_disposition = response.headers.get('Content-Disposition')
    if content_type:
        headers['Content-Type'] = content_type
    if content_disposition:
        headers['Content-Disposition'] = content_disposition
    return Response(generate(), status=response.status_code, headers=headers)

@app.route('/api/recordings/<recording_id>/status')
def get_recording_status(recording_id):
    """Get processing status for a recording"""
    status, code = api_client.get_recording_status(recording_id)
    return _json_or_error(status, code)

@app.route('/api/recordings/<recording_id>/transcript')
def get_recording_transcript(recording_id):
    """Get transcript for a recording"""
    transcript, code = api_client.get_transcript(recording_id)
    return _json_or_error(transcript, code)

@app.route('/api/recordings/<recording_id>/summary')
def get_recording_summary(recording_id):
    """Get summary for a recording"""
    summary, code = api_client.get_summary(recording_id)
    return _json_or_error(summary, code)

@app.route('/api/recordings/<recording_id>/analysis')
def get_recording_analysis(recording_id):
    """Get analysis for a recording"""
    analysis, code = api_client.get_analysis(recording_id)
    return _json_or_error(analysis, code)

@app.route('/api/refresh')
def refresh_data():
    """Force refresh of current data"""
    recordings_data, code = api_client.get_recordings()
    return _json_or_error(recordings_data, code)

if __name__ == '__main__':
    app.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)
