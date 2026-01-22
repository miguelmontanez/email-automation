import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.config import (
    FRESHA_API_KEY,
    FRESHA_BUSINESS_ID,
    FRESHA_API_BASE_URL,
    MAX_RETRIES,
    RETRY_DELAY,
)
import time

logger = logging.getLogger(__name__)


class FreshaAPIClient:
    def __init__(self):
        self.api_key = FRESHA_API_KEY
        self.business_id = FRESHA_BUSINESS_ID
        self.base_url = FRESHA_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.request(
                    method=method, url=url, headers=self.headers, timeout=30, **kwargs
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"API request failed after {MAX_RETRIES} attempts")
                    return None
            except ValueError as e:
                logger.error(f"Invalid JSON response: {e}")
                return None

    def get_today_appointments(self) -> List[Dict]:
        """Get all completed appointments for today."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            endpoint = f"/businesses/{self.business_id}/appointments"
            params = {
                "filter[start_date_min]": f"{today}T00:00:00",
                "filter[start_date_max]": f"{today}T23:59:59",
                "filter[status]": "completed",
                "limit": 100,
            }

            response = self._make_request("GET", endpoint, params=params)
            if response and "data" in response:
                return response["data"]
            return []
        except Exception as e:
            logger.error(f"Error fetching today's appointments: {e}")
            return []

    def get_appointments_for_date(self, date: str) -> List[Dict]:
        """Get appointments for a specific date."""
        try:
            endpoint = f"/businesses/{self.business_id}/appointments"
            params = {
                "filter[start_date_min]": f"{date}T00:00:00",
                "filter[start_date_max]": f"{date}T23:59:59",
                "filter[status]": "completed",
                "limit": 100,
            }

            response = self._make_request("GET", endpoint, params=params)
            if response and "data" in response:
                return response["data"]
            return []
        except Exception as e:
            logger.error(f"Error fetching appointments for {date}: {e}")
            return []

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer details."""
        try:
            endpoint = f"/businesses/{self.business_id}/customers/{customer_id}"
            return self._make_request("GET", endpoint)
        except Exception as e:
            logger.error(f"Error fetching customer {customer_id}: {e}")
            return None

    def get_customers(self, limit: int = 100) -> List[Dict]:
        """Get list of customers."""
        try:
            endpoint = f"/businesses/{self.business_id}/customers"
            params = {"limit": limit}
            
            response = self._make_request("GET", endpoint, params=params)
            if response and "data" in response:
                return response["data"]
            return []
        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return []

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Dict]:
        """Get specific appointment details."""
        try:
            endpoint = f"/businesses/{self.business_id}/appointments/{appointment_id}"
            return self._make_request("GET", endpoint)
        except Exception as e:
            logger.error(f"Error fetching appointment {appointment_id}: {e}")
            return None

    def verify_connection(self) -> bool:
        """Verify API connection and credentials."""
        try:
            endpoint = f"/businesses/{self.business_id}"
            response = self._make_request("GET", endpoint)
            if response:
                logger.info("Fresha API connection verified")
                return True
            logger.error("Failed to verify Fresha API connection")
            return False
        except Exception as e:
            logger.error(f"Error verifying API connection: {e}")
            return False
