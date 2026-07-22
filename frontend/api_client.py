import logging
import os
from typing import Dict, Optional, Tuple

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for interacting with the EzelsOor backend transcription API"""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = (base_url or os.getenv('BACKEND_API_URL', 'http://localhost:8082')).rstrip('/')
        self.timeout = timeout

    def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Tuple[Optional[Dict], int]:
        """Make a request to the backend API. Returns (payload, status_code)."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, data=data, files=files, timeout=self.timeout)
            else:
                logger.error(f"Unsupported method: {method}")
                return None, 500

            if response.status_code >= 400:
                return None, response.status_code
            try:
                return response.json(), response.status_code
            except ValueError:
                logger.error(f"Non-JSON response from {url}")
                return None, 502
        except requests.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            status = getattr(getattr(e, 'response', None), 'status_code', 502) or 502
            return None, status

    def get_recordings(self) -> Tuple[Optional[Dict], int]:
        """Get list of all recordings"""
        return self._make_request('recordings')

    def get_recording_status(self, recording_id: str) -> Tuple[Optional[Dict], int]:
        """Get processing status for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/status')

    def get_transcript(self, recording_id: str) -> Tuple[Optional[Dict], int]:
        """Get transcript for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/transcript')

    def get_summary(self, recording_id: str) -> Tuple[Optional[Dict], int]:
        """Get summary for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/summary')

    def get_analysis(self, recording_id: str) -> Tuple[Optional[Dict], int]:
        """Get language analysis for a specific recording"""
        return self._make_request(f'recordings/{recording_id}/analysis')
