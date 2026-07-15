# Meeting Transcription Dashboard

A Raspberry Pi web server for displaying audio transcription, summary, and action points data from a backend API. Features a modern UI with meeting history and participant management.

## Features

- **Real-time Transcription Display**: View current meeting transcriptions with automatic refresh
- **Summary & Action Points**: Display meeting summaries and trackable action items
- **Meeting History**: Browse and access previous meeting recordings
- **Participant Management**: View participant lists and meeting statistics
- **Modern UI**: Clean, responsive interface built with TailwindCSS
- **Auto-refresh**: Configurable automatic data refresh intervals

## Requirements

- Raspberry Pi (3B+ or recommended)
- Python 3.8+
- Network connectivity to backend API
- At least 1GB RAM
- 8GB+ SD card storage

## Installation

### 1. System Preparation

Update your Raspberry Pi system:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Python and pip:

```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 2. Clone the Repository

```bash
cd /home/pi
git clone <your-repository-url>
cd meetup-20260715
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
nano .env
```

Key configuration options:
- `BACKEND_API_URL`: Your backend transcription API endpoint
- `PORT`: Web server port (default: 8080)
- `AUTO_REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 30)

### 6. Test the Application

Run the development server:

```bash
python app.py
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
WorkingDirectory=/home/pi/meetup-20260715
Environment="PATH=/home/pi/meetup-20260715/venv/bin"
ExecStart=/home/pi/meetup-20260715/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 app:app
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

For production, use Gunicorn instead of the Flask development server:

```bash
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## Backend API Integration

The dashboard expects the backend API to provide the following endpoints:

### Required Endpoints

- `GET /api/transcription/current` - Get current/latest transcription
- `GET /api/transcription/history` - Get transcription history
- `GET /api/transcription/{id}` - Get specific transcription by ID
- `GET /api/participants` - Get participants list
- `GET /api/summary/{id}` - Get summary for a recording
- `GET /api/action-points/{id}` - Get action points for a recording

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

- **Home (`/`)**: Current transcription with summary and action points
- **History (`/history`)**: List of previous meeting recordings
- **Participants (`/participants`)**: Participant list and statistics

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
gunicorn -w 2 -b 0.0.0.0:8080 app:app
```

2. **Increase auto-refresh interval** to reduce API calls:
```bash
AUTO_REFRESH_INTERVAL=60
```

3. **Use lighter web server** like Waitress if needed:
```bash
pip install waitress
waitress-serve --port=8080 app:app
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
