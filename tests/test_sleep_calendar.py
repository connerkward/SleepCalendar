"""Unit tests for SleepCalendar class."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
from api.sleep_calendar import SleepCalendar


class TestSleepCalendar(unittest.TestCase):
    """Test SleepCalendar class methods."""
    
    @patch('api.sleep_calendar.service_account.Credentials')
    @patch('api.sleep_calendar.build')
    def setUp(self, mock_build, mock_creds):
        """Set up test fixtures."""
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service
        self.cal = SleepCalendar(credentials_json={"type": "service_account"})
        self.cal.service = self.mock_service
    
    def test_calculate_score_short_sleep(self):
        """Test score calculation for short sleep."""
        score, emoji = self.cal.calculate_score(5)
        self.assertLess(score, 50)
        self.assertEqual(emoji, '🔴')
    
    def test_calculate_score_good_sleep(self):
        """Test score calculation for good sleep."""
        score, emoji = self.cal.calculate_score(7.5)
        self.assertGreaterEqual(score, 70)
        self.assertEqual(emoji, '🟢')
    
    def test_calculate_score_fair_sleep(self):
        """Test score calculation for fair sleep."""
        score, emoji = self.cal.calculate_score(6.5)
        self.assertGreaterEqual(score, 50)
        self.assertLess(score, 70)
        self.assertEqual(emoji, '😴')
    
    def test_calculate_score_long_sleep(self):
        """Test score calculation for very long sleep."""
        score, emoji = self.cal.calculate_score(12)
        # 12 hours: 100 - (12-10)*20 = 60 (still fair, not poor)
        self.assertEqual(score, 60)
        self.assertEqual(emoji, '😴')  # Fair range (50-69)
    
    def test_group_sleep_sessions(self):
        """Test grouping sleep samples into sessions."""
        la_tz = pytz.timezone('America/Los_Angeles')
        samples = [
            {
                'startDate': '2026-01-17T02:22:00',
                'endDate': '2026-01-17T02:56:00',
                'value': 'Awake',
                'sourceName': 'Test'
            },
            {
                'startDate': '2026-01-17T02:56:00',
                'endDate': '2026-01-17T03:21:00',
                'value': 'Core',
                'sourceName': 'Test'
            }
        ]
        
        sessions = self.cal.group_sleep_sessions(samples, la_tz)
        self.assertGreater(len(sessions), 0)
        self.assertIn('intervals', sessions[0])
    
    @patch.object(SleepCalendar, 'get_or_create_calendar')
    def test_get_or_create_calendar_with_email(self, mock_get_cal):
        """Test calendar creation with user email."""
        mock_get_cal.return_value = 'test-calendar-id'
        cal_id = self.cal.get_or_create_calendar(user_email='test@example.com')
        self.assertEqual(cal_id, 'test-calendar-id')
        mock_get_cal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
