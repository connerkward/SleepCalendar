#!/usr/bin/env python3
"""Simple sleep data sync: JSON → Google Calendar with scores."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser
import pytz


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
    
    def group_sleep_sessions(self, samples, la_tz):
        """Group sleep samples into sleep sessions (one per night)."""
        # Parse all samples
        parsed = []
        for sample in samples:
            try:
                start = date_parser.parse(sample.get('startDate') or sample.get('start'))
                end = date_parser.parse(sample.get('endDate') or sample.get('end'))
                value = sample.get('value', '').strip()
                
                # Make timezone-aware if naive
                if start.tzinfo is None:
                    start = la_tz.localize(start)
                else:
                    start = start.astimezone(la_tz)
                if end.tzinfo is None:
                    end = la_tz.localize(end)
                else:
                    end = end.astimezone(la_tz)
                
                parsed.append({
                    'start': start,
                    'end': end,
                    'value': value,
                    'source': sample.get('sourceName', sample.get('source', '')).strip() or 'Apple Health'
                })
            except Exception:
                continue
        
        # Sort by start time
        parsed.sort(key=lambda x: x['start'])
        
        # Group into sessions (gaps > 2 hours = new session)
        sessions = []
        current_session = None
        
        for interval in parsed:
            if current_session is None:
                current_session = {
                    'intervals': [interval],
                    'start': interval['start'],
                    'end': interval['end']
                }
            else:
                # Check if gap is too large (new session)
                gap_hours = (interval['start'] - current_session['end']).total_seconds() / 3600
                if gap_hours > 2:
                    # Start new session
                    sessions.append(current_session)
                    current_session = {
                        'intervals': [interval],
                        'start': interval['start'],
                        'end': interval['end']
                    }
                else:
                    # Same session
                    current_session['intervals'].append(interval)
                    current_session['end'] = max(current_session['end'], interval['end'])
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
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
        
        print(f"Found {len(samples)} sleep samples")
        
        # Get/create calendar
        self.calendar_id = self.get_or_create_calendar()
        print(f"Using calendar: {self.calendar_id}")
        
        # Filter recent entries (timezone aware)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        la_tz = pytz.timezone('America/Los_Angeles')
        
        # Group into sleep sessions
        sessions = self.group_sleep_sessions(samples, la_tz)
        
        count = 0
        
        for session in sessions:
            try:
                # Filter out "Awake" intervals and calculate totals
                asleep_intervals = [i for i in session['intervals'] if i['value'] != 'Awake']
                
                if not asleep_intervals:
                    continue  # Skip sessions with no asleep time
                
                # Calculate total asleep time (excluding Awake)
                total_asleep_min = sum(
                    (i['end'] - i['start']).total_seconds() / 60
                    for i in asleep_intervals
                )
                total_asleep_hours = total_asleep_min / 60
                
                # Calculate stage breakdown
                stage_durations = {}
                for i in asleep_intervals:
                    stage = i['value']
                    dur_min = (i['end'] - i['start']).total_seconds() / 60
                    stage_durations[stage] = stage_durations.get(stage, 0) + dur_min
                
                # Session start/end (from first asleep to last asleep, not including awake)
                session_start = min(i['start'] for i in asleep_intervals)
                session_end = max(i['end'] for i in asleep_intervals)
                
                # Convert to UTC for cutoff comparison
                session_start_utc = session_start.astimezone(timezone.utc)
                if session_start_utc < cutoff:
                    continue
                
                # Calculate score based on total asleep time
                score, emoji = self.calculate_score(total_asleep_hours)
                
                # Score description
                if score >= 70:
                    score_desc = 'Good (ideal 7-8 hours)'
                elif score >= 50:
                    score_desc = 'Fair (6-7 hours)'
                else:
                    score_desc = 'Poor (<6 hours or >10 hours)'
                
                # Format stage breakdown
                stage_breakdown = []
                for stage in ['Core', 'Deep', 'REM']:
                    if stage in stage_durations:
                        mins = stage_durations[stage]
                        hours = mins / 60
                        stage_breakdown.append(f'{stage}: {int(mins)} min ({hours:.1f} hr)')
                
                # Get source (use most common source from intervals)
                sources = [i.get('source', 'Apple Health') for i in asleep_intervals]
                source = max(set(sources), key=sources.count) if sources else 'Apple Health'
                
                # Create description
                description_lines = [
                    f'Sleep Score: {score}/100 ({score_desc})',
                    f'',
                    f'Time Asleep: {total_asleep_hours:.1f} hours ({int(total_asleep_min)} min)',
                    f'Source: {source}',
                    f'',
                    f'Stage Breakdown:'
                ]
                description_lines.extend(stage_breakdown)
                description_lines.extend([
                    f'',
                    f'Score Breakdown:',
                    f'🟢 70-100: Good sleep (7-8 hours ideal)',
                    f'😴 50-69: Fair sleep (6-7 hours)',
                    f'🔴 0-49: Poor sleep (<6 hours or >10 hours)'
                ])
                
                event = {
                    'summary': f'{emoji} Sleep ({total_asleep_hours:.1f}h)',
                    'description': '\n'.join(description_lines),
                    'start': {'dateTime': session_start.isoformat(), 'timeZone': 'America/Los_Angeles'},
                    'end': {'dateTime': session_end.isoformat(), 'timeZone': 'America/Los_Angeles'},
                }
                
                # Check if aggregated event exists (look for summary pattern with emoji + "Sleep")
                time_min = (session_start - timedelta(minutes=5)).isoformat()
                time_max = (session_end + timedelta(minutes=5)).isoformat()
                existing_events = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True
                ).execute()
                
                # Check specifically for aggregated event (emoji + "Sleep" in summary)
                aggregated_exists = False
                for existing in existing_events.get('items', []):
                    summary = existing.get('summary', '')
                    # Look for aggregated event pattern: emoji + "Sleep (X.Xh)"
                    if ('Sleep' in summary and ('🟢' in summary or '😴' in summary or '🔴' in summary)) and 'h)' in summary:
                        aggregated_exists = True
                        break
                
                # If aggregated event doesn't exist, create it
                if not aggregated_exists:
                    try:
                        self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
                        count += 1
                        print(f"Created aggregated event: {session_start.strftime('%m/%d %H:%M')} - {total_asleep_hours:.1f}h")
                    except HttpError as e:
                        print(f"Error inserting aggregated event: {e}")
                
                # Create separate events for each stage interval
                stage_emojis = {
                    'Core': '💙',
                    'Deep': '💜',
                    'REM': '💤',
                    'Awake': '🔴'
                }
                
                for interval in session['intervals']:
                    stage = interval['value']
                    if not stage:  # Skip if no stage value
                        continue
                    
                    interval_start = interval['start']
                    interval_end = interval['end']
                    duration_min = (interval_end - interval_start).total_seconds() / 60
                    duration_hours = duration_min / 60
                    
                    # Emoji for this stage
                    stage_emoji = stage_emojis.get(stage, '⏱')
                    
                    # Create stage event
                    stage_event = {
                        'summary': f'{stage_emoji} {stage} ({duration_hours:.1f}h)',
                        'description': f'Stage: {stage}\nDuration: {duration_min:.0f} min ({duration_hours:.1f} hours)\nSource: {interval.get("source", "Apple Health")}',
                        'start': {'dateTime': interval_start.isoformat(), 'timeZone': 'America/Los_Angeles'},
                        'end': {'dateTime': interval_end.isoformat(), 'timeZone': 'America/Los_Angeles'},
                    }
                    
                    # Check if this specific stage event exists (within 1 minute)
                    stage_time_min = (interval_start - timedelta(minutes=1)).isoformat()
                    stage_time_max = (interval_end + timedelta(minutes=1)).isoformat()
                    existing_stage_events = self.service.events().list(
                        calendarId=self.calendar_id,
                        timeMin=stage_time_min,
                        timeMax=stage_time_max,
                        singleEvents=True
                    ).execute()
                    
                    # Check if an event with this summary already exists in this time window
                    stage_exists = False
                    for existing in existing_stage_events.get('items', []):
                        if existing.get('summary', '').startswith(stage_emoji) or stage in existing.get('summary', ''):
                            stage_exists = True
                            break
                    
                    if not stage_exists:
                        try:
                            self.service.events().insert(calendarId=self.calendar_id, body=stage_event).execute()
                            count += 1
                        except HttpError as e:
                            print(f"Error inserting stage event ({stage}): {e}")
                
            except Exception as e:
                print(f"Skip session: {e}")
                continue
        
        print(f"✅ Synced {count} events ({len(sessions)} aggregated + stage events)")
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
