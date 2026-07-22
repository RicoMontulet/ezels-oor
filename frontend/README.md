# Meeting Transcription Dashboard

A web dashboard for displaying audio transcription, summary, and action points data from a backend API. Features a modern UI with meeting history, participant management, and audio recording capabilities.

## Architecture

The application consists of three components:

### 1. Frontend Dashboard (Port 8080)
- **Purpose**: Main web interface for viewing transcriptions and managing recordings
- **Technology**: Flask, Jinja2 templates, TailwindCSS
- **Responsibilities**:
  - Display transcription data from backend API
  - Proxy recording API calls to local recording app
  - Provide user interface for all features

### 2. Local Recording App (Port 5000)
- **Purpose**: Handle audio recording and upload to backend
- **Technology**: Flask, audio recording libraries
- **Responsibilities**:
  - Manage audio device detection and recording
  - Store temporary audio files
  - Upload recordings to backend API
  - Provide recording status and file serving

### 3. Backend API (Port 8081)
- **Purpose**: Process audio transcriptions and provide results
- **Technology**: REST API
- **Responsibilities**:
  - Receive and process audio recordings
  - Generate transcriptions
  - Create summaries and action items
  - Provide language analysis

## Features

- **Audio Recording**: Record audio directly from the browser with device management
- **Real-time Transcription Display**: View current meeting transcriptions with automatic refresh
- **Summary & Action Points**: Display meeting summaries and trackable action items
- **Meeting History**: Browse and access previous meeting recordings
- **Participant Management**: View speaker lists and statistics extracted from transcriptions
- **Modern UI**: Clean, responsive interface built with TailwindCSS
- **Auto-refresh**: Configurable automatic data refresh intervals

## Requirements

- Raspberry Pi (3B+ or recommended)
- Python 3.8+
- Network connectivity to backend API
- At least 1GB RAM
- 8GB+ SD card storage
- uv package manager (recommended for faster dependency management)

## Installation

### 1. System Preparation

Update your Raspberry Pi system:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Python:

```bash
sudo apt install python3 -y
```

Install uv package manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
cd /home/pi
git clone <your-repository-url>
cd meetup-20260715/frontend
```

### 3. Install Dependencies with uv

```bash
uv sync
```

This will create a virtual environment and install all dependencies from `pyproject.toml`.

### 4. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
nano .env
```

Key configuration options:
- `BACKEND_API_URL`: Your backend transcription API endpoint (default: http://localhost:8081)
- `RECORDING_APP_URL`: Local recording app endpoint (default: http://localhost:5000)
- `PORT`: Web server port (default: 8080)
- `AUTO_REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 30)

### 5. Test the Application

Run the development server with uv:

```bash
uv run python app.py
```

Access the dashboard at `http://<your-pi-ip>:8080`

## Production Deployment

### Using Systemd Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/meeting-dashboard.service
```

Add the following content:

```ini
[Unit]
Description=Meeting Transcription Dashboard
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/meetup-20260715/frontend
ExecStart=/home/pi/.local/bin/uv run gunicorn -w 4 -b 0.0.0.0:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable meeting-dashboard
sudo systemctl start meeting-dashboard
```

Check service status:

```bash
sudo systemctl status meeting-dashboard
```

### Using Gunicorn

For production, use Gunicorn with uv instead of the Flask development server:

```bash
uv run gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## Screen-to-API Connections

### Home Page (`/`)
**Frontend → Backend API:**
- `GET /recordings` - Fetch list of all recordings
- `GET /recordings/{id}/transcript` - Get transcript for latest recording
- `GET /recordings/{id}/summary` - Get summary for latest recording

**Frontend → Recording App:**
- None (this page only displays data)

### History Page (`/history`)
**Frontend → Backend API:**
- `GET /recordings` - Fetch list of all recordings
- `GET /recordings/{id}/status` - Get processing status for each recording

**Frontend → Recording App:**
- None (this page only displays data)

### Participants Page (`/participants`)
**Frontend → Backend API:**
- `GET /recordings` - Fetch list of recordings
- `GET /recordings/{id}/transcript` - Get transcript to extract speakers

**Frontend → Recording App:**
- None (this page only displays data)

### Recording Page (`/record`)
**Frontend → Recording App (via Frontend Proxy):**
- `GET /api/status` - Check recording status and device state
- `POST /api/record/start` - Start audio recording
- `POST /api/record/stop` - Stop audio recording
- `POST /api/record/send` - Send last recording to backend API
- `GET /api/recording/file` - Play/download last recording

**Frontend → Backend API:**
- None (recording app handles backend communication)

### Recording Detail Page (`/recording/{id}`)
**Frontend → Backend API:**
- `GET /recordings` - Fetch list to find specific recording
- `GET /recordings/{id}/transcript` - Get transcript
- `GET /recordings/{id}/summary` - Get summary
- `GET /recordings/{id}/analysis` - Get language analysis
- `GET /recordings/{id}/status` - Get processing status

**Frontend → Recording App:**
- None (this page only displays data)

### About Page (`/about`)
**Frontend → Backend API:**
- None (static content page)

**Frontend → Recording App:**
- None (static content page)

## API Proxy Routes

The frontend dashboard acts as a proxy for recording app endpoints:

| Frontend Route | Recording App Route | Method | Purpose |
|----------------|---------------------|--------|---------|
| `/api/status` | `/api/status` | GET | Check recording status |
| `/api/record/start` | `/api/record/start` | POST | Start recording |
| `/api/record/stop` | `/api/record/stop` | POST | Stop recording |
| `/api/record/send` | `/api/record/send` | POST | Send to backend |
| `/api/recording/file` | `/api/recording/file` | GET | Serve audio file |

## Backend API Integration

The dashboard expects the backend API to provide the following endpoints:

### Required Endpoints

- `GET /recordings` - Get list of all recordings
- `GET /recordings/{id}/status` - Get processing status for a recording
- `GET /recordings/{id}/transcript` - Get transcript for a recording
- `GET /recordings/{id}/summary` - Get summary for a recording
- `GET /recordings/{id}/analysis` - Get language analysis for a recording

### Expected Data Format

#### Transcription Response
```json
{
  "id": "string",
  "text": "string",
  "summary": "string",
  "action_points": [
    {
      "text": "string",
      "assignee": "string",
      "due_date": "string",
      "priority": "high|medium|low"
    }
  ],
  "participants": [
    {
      "name": "string",
      "role": "string"
    }
  ],
  "metadata": {
    "duration": "string",
    "language": "string"
  }
}
```

#### History Response
```json
[
  {
    "id": "string",
    "title": "string",
    "date": "string",
    "duration": "string",
    "participant_count": number,
    "action_points_count": number,
    "summary": "string"
  }
]
```

#### Participants Response
```json
[
  {
    "name": "string",
    "email": "string",
    "role": "string",
    "meeting_count": number,
    "last_meeting": "string",
    "active": boolean
  }
]
```

## Usage

### Accessing the Dashboard

Once running, access the dashboard from any device on your network:

```
http://<raspberry-pi-ip>:8080
```

### Pages

- **Home (`/`)**: Latest recording with transcript, summary, and action items
- **History (`/history`)**: List of all recordings with processing status
- **Participants (`/participants`)**: Speaker list extracted from latest recording
- **Record (`/record`)**: Audio recording interface with start/stop/send controls
- **Recording Detail (`/recording/{id}`)**: Detailed view of a specific recording
- **About (`/about`)**: Information about the application

### Auto-refresh

The dashboard automatically refreshes every 30 seconds (configurable). You can also manually refresh using the refresh button on each page.

## Troubleshooting

### Service won't start

Check the service logs:
```bash
sudo journalctl -u meeting-dashboard -f
```

### Can't access the dashboard

1. Check if the service is running:
```bash
sudo systemctl status meeting-dashboard
```

2. Verify the port is not blocked:
```bash
sudo netstat -tlnp | grep 8080
```

3. Check firewall settings:
```bash
sudo ufw status
```

### Backend API connection issues

1. Verify the backend API URL in `.env`
2. Check network connectivity:
```bash
curl http://<backend-api-url>/api/transcription/current
```

3. Check application logs for specific error messages

## Performance Optimization

For better performance on Raspberry Pi:

1. **Reduce worker count** in Gunicorn if memory is limited:
```bash
uv run gunicorn -w 2 -b 0.0.0.0:8080 app:app
```

2. **Increase auto-refresh interval** to reduce API calls:
```bash
AUTO_REFRESH_INTERVAL=60
```

3. **Use lighter web server** like Waitress if needed:
```bash
uv add waitress
uv run waitress-serve --port=8080 app:app
```

## Security Considerations

- Change the default `SECRET_KEY` in production
- Use HTTPS in production environments
- Implement authentication if the dashboard is publicly accessible
- Keep the system and dependencies updated
- Use a firewall to restrict access if needed

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the repository or contact [your contact information].
