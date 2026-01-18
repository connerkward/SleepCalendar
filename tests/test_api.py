"""Unit tests for API endpoints."""
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.server import app


class TestAPI(unittest.TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    @patch('api.server.SleepCalendar')
    def test_sync_endpoint_success(self, mock_cal_class):
        """Test successful sync endpoint."""
        mock_cal = MagicMock()
        mock_cal.calendar_id = "test-calendar-id"
        mock_cal.sync_from_data.return_value = 5
        mock_cal_class.return_value = mock_cal
        
        request_data = {
            "email": "test@example.com",
            "samples": [
                {
                    "startDate": "2026-01-17T02:22:00",
                    "endDate": "2026-01-17T02:56:00",
                    "value": "Core",
                    "sourceName": "Test"
                }
            ]
        }
        
        response = self.client.post("/sync", json=request_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["events_synced"], 5)
        self.assertEqual(data["calendar_id"], "test-calendar-id")
    
    def test_sync_endpoint_invalid_email(self):
        """Test sync endpoint with invalid email."""
        request_data = {
            "email": "invalid-email",
            "samples": []
        }
        
        response = self.client.post("/sync", json=request_data)
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_sync_endpoint_missing_fields(self):
        """Test sync endpoint with missing fields."""
        request_data = {
            "email": "test@example.com"
            # Missing samples
        }
        
        response = self.client.post("/sync", json=request_data)
        self.assertEqual(response.status_code, 422)  # Validation error


if __name__ == '__main__':
    unittest.main()
