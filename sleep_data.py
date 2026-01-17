#!/usr/bin/env python3
"""Simple sleep data sync: JSON → Google Calendar with scores."""

import json
import os
import sys
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser


class SleepCalendar:
    """Sync sleep data to Google Calendar."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path='service-account.json', share_emails=None):
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES)
        self.service = build('calendar', 'v3', credentials=self.creds)
        self.calendar_id = None
        self.share_emails = share_emails or os.getenv('SHARE_WITH_EMAILS', '').split(',')
    
    def get_or_create_calendar(self, name='Sleep Data'):
        """Get or create calendar."""
        # List calendars
        calendars = self.service.calendarList().list().execute()
        for cal in calendars.get('items', []):
            if cal.get('summary') == name:
                return cal['id']
        
        # Create new
        calendar = {'summary': name, 'timeZone': 'America/Los_Angeles'}
        created = self.service.calendars().insert(body=calendar).execute()
        cal_id = created['id']
        
        # Make public read-only (for easy subscription in Google Calendar)
        acl = {'scope': {'type': 'default'}, 'role': 'reader'}
        self.service.acl().insert(calendarId=cal_id, body=acl).execute()
        
        # Share with emails (if provided) for write access
        for email in self.share_emails:
            if email.strip():
                try:
                    user_acl = {'scope': {'type': 'user', 'value': email.strip()}, 'role': 'writer'}
                    self.service.acl().insert(calendarId=cal_id, body=user_acl).execute()
                except HttpError:
                    pass
        
        return cal_id
    
    def calculate_score(self, duration_hours):
        """Calculate sleep score (0-100) and emoji."""
        if duration_hours < 6:
            score = (duration_hours / 6) * 50
        elif duration_hours > 10:
            score = max(0, 100 - (duration_hours - 10) * 20)
        else:
            # 6-8 hours ideal
            if duration_hours <= 8:
                score = 50 + (duration_hours - 6) / 2 * 50
            else:
                score = 100 - (duration_hours - 8) / 2 * 10
        
        # Emoji
        if score >= 70:
            emoji = '🟢'
        elif score >= 50:
            emoji = '😴'
        else:
            emoji = '🔴'
        
        return int(score), emoji
    
    def sync(self, json_file='export.json', days=30):
        """Sync sleep data to calendar."""
        # Read JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Handle different formats
        samples = data if isinstance(data, list) else data.get('samples', [])
        
        # If samples is a string (newline-delimited JSON), parse it
        if isinstance(samples, str):
            samples = [json.loads(line) for line in samples.strip().split('\n') if line.strip()]
        
        print(f"Found {len(samples)} sleep entries")
        
        # Get/create calendar
        self.calendar_id = self.get_or_create_calendar()
        print(f"Using calendar: {self.calendar_id}")
        
        # Filter recent entries (timezone aware)
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        count = 0
        
        for sample in samples:
            try:
                start = date_parser.parse(sample.get('startDate') or sample.get('start'))
                end = date_parser.parse(sample.get('endDate') or sample.get('end'))
                
                if start < cutoff:
                    continue
                
                # Calculate score
                duration = (end - start).total_seconds() / 3600
                score, emoji = self.calculate_score(duration)
                
                # Create event
                source = sample.get('sourceName', sample.get('source', 'Unknown'))
                event = {
                    'summary': f'{emoji} Sleep ({duration:.1f}h)',
                    'description': f'Score: {score}\nSource: {source}\nDuration: {duration:.1f} hours',
                    'start': {'dateTime': start.isoformat(), 'timeZone': 'America/Los_Angeles'},
                    'end': {'dateTime': end.isoformat(), 'timeZone': 'America/Los_Angeles'},
                }
                
                # Check if event exists for this time window (within 1 minute)
                time_min = (start - timedelta(minutes=1)).isoformat()
                time_max = (end + timedelta(minutes=1)).isoformat()
                existing_events = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True
                ).execute()
                
                # If event exists, skip to preserve manual edits
                # If not, insert new event
                if not existing_events.get('items'):
                    try:
                        self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
                        count += 1
                    except HttpError as e:
                        print(f"Error inserting event: {e}")
                # else: event exists, skip (preserves manual edits)
                
            except Exception as e:
                print(f"Skip entry: {e}")
                continue
        
        print(f"✅ Synced {count} events")
        print(f"📅 Calendar: https://calendar.google.com/calendar/embed?src={self.calendar_id}")
        return count


def main():
    """Main entry point."""
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'export.json'
    
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found")
        return 1
    
    cal = SleepCalendar()
    cal.sync(json_file)
    return 0


if __name__ == '__main__':
    sys.exit(main())
