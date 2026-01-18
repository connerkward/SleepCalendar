"""Integration tests for sleep calendar sync (optional, requires credentials)."""
import unittest
import os


class TestIntegration(unittest.TestCase):
    """Integration tests - requires valid service account credentials."""
    
    def setUp(self):
        """Skip if credentials not available."""
        if not os.getenv('GOOGLE_CALENDAR_CREDENTIALS'):
            self.skipTest("GOOGLE_CALENDAR_CREDENTIALS not set")
    
    @unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), "Integration tests disabled")
    def test_real_calendar_creation(self):
        """Test real calendar creation (requires credentials)."""
        from api.sleep_calendar import SleepCalendar
        
        cal = SleepCalendar(user_email="test@example.com")
        cal_id = cal.get_or_create_calendar(user_email="test@example.com")
        
        self.assertIsNotNone(cal_id)
        self.assertTrue(cal_id.endswith('@group.calendar.google.com'))


if __name__ == '__main__':
    unittest.main()
