"""Google Calendar integration."""

import os
from datetime import datetime, timedelta
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apple_health_parser import SleepEntry
from sleep_analyzer import SleepAnalyzer


class CalendarManager:
    """Manage Google Calendar syncing."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str, share_with_emails: Optional[List[str]] = None,
                 calendar_name_iphone: str = "Sleep - iPhone",
                 calendar_name_withings: str = "Sleep - Withings",
                 calendar_name_merged: str = "Sleep - Merged"):
        self.credentials_path = credentials_path
        self.share_with_emails = share_with_emails or []
        self.calendar_name_iphone = calendar_name_iphone
        self.calendar_name_withings = calendar_name_withings
        self.calendar_name_merged = calendar_name_merged
        self.service = None
        self.calendar_id_iphone = None
        self.calendar_id_withings = None
        self.calendar_id_merged = None
        self.analyzer = SleepAnalyzer()
    
    def authenticate(self):
        """Authenticate with Google Calendar."""
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.SCOPES)
        self.service = build('calendar', 'v3', credentials=creds)
    
    def ensure_calendars_exist(self):
        """Create calendars if they don't exist."""
        self.calendar_id_iphone = self._get_or_create_calendar(self.calendar_name_iphone)
        self.calendar_id_withings = self._get_or_create_calendar(self.calendar_name_withings)
        self.calendar_id_merged = self._get_or_create_calendar(self.calendar_name_merged)
        return {
            'iphone': self.calendar_id_iphone,
            'withings': self.calendar_id_withings,
            'merged': self.calendar_id_merged
        }
    
    def _get_or_create_calendar(self, name: str) -> str:
        """Get or create calendar."""
        # List calendars
        calendars = self.service.calendarList().list().execute()
        for calendar in calendars.get('items', []):
            if calendar.get('summary') == name:
                return calendar['id']
        
        # Create new calendar
        calendar = {
            'summary': name,
            'timeZone': 'America/Los_Angeles'
        }
        created = self.service.calendars().insert(body=calendar).execute()
        calendar_id = created['id']
        
        # Make public (read-only)
        acl = {'scope': {'type': 'default'}, 'role': 'reader'}
        self.service.acl().insert(calendarId=calendar_id, body=acl).execute()
        
        # Share with specific emails
        for email in self.share_with_emails:
            try:
                user_acl = {'scope': {'type': 'user', 'value': email}, 'role': 'writer'}
                self.service.acl().insert(calendarId=calendar_id, body=user_acl).execute()
            except HttpError:
                pass
        
        return calendar_id
    
    def sync_entries_to_calendar(self, entries: List[SleepEntry], calendar_id: str, days: int = 30) -> int:
        """Sync sleep entries to calendar."""
        cutoff = datetime.now() - timedelta(days=days)
        recent_entries = [e for e in entries if e.start_date >= cutoff]
        
        for entry in recent_entries:
            score = self.analyzer.calculate_score(entry)
            event = {
                'summary': f'{score.emoji} Sleep ({entry.duration_minutes/60:.1f}h)',
                'description': f'Score: {score.score:.0f}\\nSource: {entry.source}\\nDevice: {entry.device}',
                'start': {'dateTime': entry.start_date.isoformat(), 'timeZone': 'America/Los_Angeles'},
                'end': {'dateTime': entry.end_date.isoformat(), 'timeZone': 'America/Los_Angeles'},
            }
            
            try:
                self.service.events().insert(calendarId=calendar_id, body=event).execute()
            except HttpError:
                pass
        
        return len(recent_entries)
    
    def get_calendar_feed_url(self, calendar_id: str) -> str:
        """Get iCal feed URL."""
        return f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics"
