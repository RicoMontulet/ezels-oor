import logging
import os
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendAPIClient:
    """Client for interacting with the backend transcription API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')
        self.timeout = 10

    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the backend API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, json=params, timeout=self.timeout)
            else:
                logger.error(f"Unsupported method: {method}")
                return None

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return None

    def get_current_transcription(self) -> Optional[Dict]:
        """Get the current/latest transcription"""
        return self._make_request('transcription/current')

    def get_transcription_by_id(self, recording_id: str) -> Optional[Dict]:
        """Get a specific transcription by recording ID"""
        return self._make_request(f'transcription/{recording_id}')

    def get_transcription_history(self, limit: int = 20) -> Optional[List[Dict]]:
        """Get history of transcriptions"""
        return self._make_request('transcription/history', params={'limit': limit})

    def get_participants(self, recording_id: Optional[str] = None) -> Optional[List[Dict]]:
        """Get participants list, optionally filtered by recording"""
        params = {'recording_id': recording_id} if recording_id else None
        return self._make_request('participants', params=params)

    def get_summary(self, recording_id: str) -> Optional[Dict]:
        """Get summary for a specific recording"""
        return self._make_request(f'summary/{recording_id}')

    def get_action_points(self, recording_id: str) -> Optional[List[Dict]]:
        """Get action points for a specific recording"""
        return self._make_request(f'action-points/{recording_id}')

    def get_recording_metadata(self, recording_id: str) -> Optional[Dict]:
        """Get metadata for a specific recording"""
        return self._make_request(f'recording/{recording_id}/metadata')
