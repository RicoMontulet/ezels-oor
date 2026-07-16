import logging
import os
from typing import Dict, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendAPIClient:
    """Client for interacting with the EzelsOor backend transcription API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('BACKEND_API_URL', 'http://localhost:8081')
        self.timeout = 30

    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None,
                     data: Optional[Dict] = None, files: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the backend API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, data=data, files=files, timeout=self.timeout)
            else:
                logger.error(f"Unsupported method: {method}")
                return None

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return None

    def get_recordings(self) -> Optional[Dict]:
        """Get list of all recordings"""
        return self._make_request('recordings')

    def get_recording_status(self, recording_id: str) -> Optional[Dict]:
        """Get processing status for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/status')

    def get_transcript(self, recording_id: str) -> Optional[Dict]:
        """Get transcript for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/transcript')

    def get_summary(self, recording_id: str) -> Optional[Dict]:
        """Get summary for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/summary')

    def get_analysis(self, recording_id: str) -> Optional[Dict]:
        """Get language analysis for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/analysis')
