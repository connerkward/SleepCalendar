#!/usr/bin/env python3
"""Sleep calendar sync logic for API - supports per-user calendars."""

import json
import os
import base64
import io
import sys
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser
import pytz


class SleepCalendar:
    """Sync sleep data to Google Calendar with per-user calendar support."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path=None, credentials_json=None, user_email=None):
        """
        Initialize SleepCalendar.
        
        Args:
            credentials_path: Path to service account JSON file (optional)
            credentials_json: Service account JSON as dict or string (optional)
            user_email: User email for calendar identification (optional)
        """
        # Priority: credentials_json > credentials_path > env var
        if credentials_json:
            if isinstance(credentials_json, str):
                # Try parsing as JSON string
                try:
                    credentials_json = json.loads(credentials_json)
                except json.JSONDecodeError:
                    # Try base64 decode
                    try:
                        decoded = base64.b64decode(credentials_json).decode('utf-8')
                        credentials_json = json.loads(decoded)
                    except Exception:
                        raise ValueError("Invalid credentials_json format")
            self.creds = service_account.Credentials.from_service_account_info(
                credentials_json, scopes=self.SCOPES)
        elif credentials_path:
            self.creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=self.SCOPES)
        else:
            # Try env var (base64 or JSON string)
            creds_env = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
            if creds_env:
                try:
                    # Try base64 decode first
                    decoded = base64.b64decode(creds_env).decode('utf-8')
                    creds_dict = json.loads(decoded)
                except Exception:
                    # Fall back to direct JSON
                    creds_dict = json.loads(creds_env)
                self.creds = service_account.Credentials.from_service_account_info(
                    creds_dict, scopes=self.SCOPES)
            else:
                # Fall back to default file path
                self.creds = service_account.Credentials.from_service_account_file(
                    'service-account.json', scopes=self.SCOPES)
        
        self.service = build('calendar', 'v3', credentials=self.creds)
        self.calendar_id = None
        self.user_email = user_email
    
    def get_or_create_calendar(self, name=None, user_email=None):
        """
        Get or create calendar. If user_email is provided, creates per-user calendar.
        
        Args:
            name: Calendar name (default: "Sleep Data" or "Sleep Data - {user_email}")
            user_email: User email for per-user calendar (defaults to self.user_email)
        """
        user_email = user_email or self.user_email
        
        # Determine calendar name
        if name is None:
            if user_email:
                name = f"Sleep Data - {user_email}"
            else:
                name = "Sleep Data"
        
        # List calendars
        calendars = self.service.calendarList().list().execute()
        for cal in calendars.get('items', []):
            if cal.get('summary') == name:
                self.calendar_id = cal['id']
                return cal['id']
        
        # Create new
        calendar = {'summary': name, 'timeZone': 'America/Los_Angeles'}
        created = self.service.calendars().insert(body=calendar).execute()
        cal_id = created['id']
        self.calendar_id = cal_id
        
        # Make public read-only (for easy subscription in Google Calendar)
        acl = {'scope': {'type': 'default'}, 'role': 'reader'}
        self.service.acl().insert(calendarId=cal_id, body=acl).execute()
        
        # Share with user email (writer role) if provided
        if user_email:
            try:
                user_acl = {'scope': {'type': 'user', 'value': user_email}, 'role': 'writer'}
                self.service.acl().insert(calendarId=cal_id, body=user_acl).execute()
            except HttpError as e:
                # Log but don't fail if sharing fails
                print(f"Warning: Could not share calendar with {user_email}: {e}", file=sys.stderr)
        
        return cal_id
    
    def calculate_score(self, duration_hours):
        """Calculate sleep score (0-100) and emoji."""
        if duration_hours < 6:
            score = (duration_hours / 6) * 50
        elif duration_hours > 10:
            score = max(0, 100 - (duration_hours - 10) * 20)
        else:
            if duration_hours <= 8:
                score = 50 + (duration_hours - 6) / 2 * 50
            else:
                score = 100 - (duration_hours - 8) / 2 * 10
        
        if score >= 70:
            emoji = '🟢'
        elif score >= 50:
            emoji = '😴'
        else:
            emoji = '🔴'
        
        return int(score), emoji
    
    def group_sleep_sessions(self, samples, la_tz):
        """Group sleep samples into sleep sessions (one per night)."""
        parsed_samples = []
        for sample in samples:
            try:
                start_raw = sample.get('startDate') or sample.get('start')
                end_raw = sample.get('endDate') or sample.get('end')
                if not start_raw or not end_raw:
                    continue
                
                start = date_parser.parse(start_raw)
                end = date_parser.parse(end_raw)
                
                if start.tzinfo is None:
                    start = la_tz.localize(start)
                else:
                    start = start.astimezone(la_tz)
                if end.tzinfo is None:
                    end = la_tz.localize(end)
                else:
                    end = end.astimezone(la_tz)
                
                parsed_samples.append({
                    'start': start,
                    'end': end,
                    'value': str(sample.get('value', 'Unknown')).strip(),
                    'source': sample.get('sourceName', sample.get('source', '')).strip() or 'Apple Health'
                })
            except Exception:
                continue
        
        parsed_samples.sort(key=lambda x: x['start'])
        
        sessions = []
        current_session = None
        
        for sample in parsed_samples:
            if current_session is None:
                current_session = {'start': sample['start'], 'end': sample['end'], 'intervals': [sample]}
            else:
                time_diff = sample['start'] - current_session['end']
                if time_diff <= timedelta(hours=2) and time_diff >= timedelta(minutes=-30):
                    current_session['end'] = max(current_session['end'], sample['end'])
                    current_session['intervals'].append(sample)
                else:
                    sessions.append(current_session)
                    current_session = {'start': sample['start'], 'end': sample['end'], 'intervals': [sample]}
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    def sync_from_data(self, data, user_email=None, days=30):
        """
        Sync sleep data from dict/list directly (not from file).
        
        Args:
            data: Dict with 'samples' key or list of samples
            user_email: User email for calendar identification
            days: Number of days to look back for cutoff
            
        Returns:
            int: Number of events synced
        """
        user_email = user_email or self.user_email
        self.user_email = user_email
        
        # Handle different formats
        if isinstance(data, dict) and 'samples' in data:
            samples_raw = data['samples']
        elif isinstance(data, list):
            samples_raw = data
        else:
            samples_raw = []
        
        # If samples is a string (newline-delimited JSON), parse it
        if isinstance(samples_raw, str):
            samples = [json.loads(line) for line in samples_raw.strip().split('\n') if line.strip()]
        elif isinstance(samples_raw, list):
            samples = samples_raw
        else:
            samples = []
        
        # Get/create calendar for this user
        self.calendar_id = self.get_or_create_calendar(user_email=user_email)
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        la_tz = pytz.timezone('America/Los_Angeles')
        
        sessions = self.group_sleep_sessions(samples, la_tz)
        count = 0
        
        for session in sessions:
            try:
                valid_stages = {'Core', 'Deep', 'REM'}
                asleep_intervals = []
                awake_intervals = []
                
                for i in session['intervals']:
                    value = str(i.get('value', '')).strip()
                    if value in valid_stages:
                        asleep_intervals.append(i)
                    elif value.lower() == 'awake':
                        awake_intervals.append(i)
                
                if not asleep_intervals:
                    continue
                
                total_asleep_min = sum(
                    (i['end'] - i['start']).total_seconds() / 60
                    for i in asleep_intervals
                )
                total_asleep_hours = total_asleep_min / 60
                
                stage_durations = {}
                for i in asleep_intervals:
                    stage = i['value']
                    dur_min = (i['end'] - i['start']).total_seconds() / 60
                    stage_durations[stage] = stage_durations.get(stage, 0) + dur_min
                
                aggregated_start = min(i['start'] for i in asleep_intervals)
                aggregated_end = max(i['end'] for i in asleep_intervals)
                
                session_start = min(i['start'] for i in session['intervals'])
                session_end = max(i['end'] for i in session['intervals'])
                
                session_start_utc = session_start.astimezone(timezone.utc)
                if session_start_utc < cutoff:
                    continue
                
                score, emoji = self.calculate_score(total_asleep_hours)
                
                if score >= 70:
                    score_desc = 'Good (ideal 7-8 hours)'
                elif score >= 50:
                    score_desc = 'Fair (6-7 hours)'
                else:
                    score_desc = 'Poor (<6 hours or >10 hours)'
                
                stage_breakdown_lines = []
                for stage_name in ['Core', 'Deep', 'REM']:
                    if stage_name in stage_durations:
                        mins = stage_durations[stage_name]
                        stage_breakdown_lines.append(f'{stage_name}: {int(mins)} min ({mins/60:.1f} hr)')
                
                awake_total_min = sum((i['end'] - i['start']).total_seconds() / 60 for i in awake_intervals) if awake_intervals else 0
                if awake_total_min > 0:
                    stage_breakdown_lines.append(f'Awake: {int(awake_total_min)} min ({awake_total_min/60:.1f} hr)')
                
                all_sources = [i.get('source', 'Apple Health') for i in session['intervals']]
                source = max(set(all_sources), key=all_sources.count) if all_sources else 'Apple Health'
                
                description_lines = [
                    f'Sleep Score: {score}/100 ({score_desc})',
                    f'',
                    f'Time Asleep: {total_asleep_hours:.1f} hours ({int(total_asleep_min)} min)',
                    f'Source: {source}',
                    f'',
                    f'Stage Breakdown:'
                ]
                description_lines.extend(stage_breakdown_lines)
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
                    'start': {'dateTime': aggregated_start.isoformat(), 'timeZone': 'America/Los_Angeles'},
                    'end': {'dateTime': aggregated_end.isoformat(), 'timeZone': 'America/Los_Angeles'},
                }
                
                time_min = (aggregated_start - timedelta(minutes=5)).isoformat()
                time_max = (aggregated_end + timedelta(minutes=5)).isoformat()
                existing_events = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True
                ).execute()
                
                aggregated_exists = False
                for existing in existing_events.get('items', []):
                    summary = existing.get('summary', '')
                    if ('Sleep' in summary and ('🟢' in summary or '😴' in summary or '🔴' in summary)) and 'h)' in summary:
                        aggregated_exists = True
                        break
                
                if not aggregated_exists:
                    try:
                        self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
                        count += 1
                    except HttpError as e:
                        print(f"Error inserting aggregated event: {e}", file=sys.stderr)
                
                stage_emojis = {
                    'Core': '💙',
                    'Deep': '💜',
                    'REM': '💤',
                    'Awake': '🔴'
                }
                
                for interval in session['intervals']:
                    stage = interval['value']
                    if not stage:
                        continue
                    
                    interval_start = interval['start']
                    interval_end = interval['end']
                    duration_min = (interval_end - interval_start).total_seconds() / 60
                    duration_hours = duration_min / 60
                    
                    stage_emoji = stage_emojis.get(stage, '⏱')
                    
                    stage_event = {
                        'summary': f'{stage_emoji} {stage} ({duration_hours:.1f}h)',
                        'description': f'Stage: {stage}\nDuration: {duration_min:.0f} min ({duration_hours:.1f} hours)\nSource: {interval.get("source", "Apple Health")}',
                        'start': {'dateTime': interval_start.isoformat(), 'timeZone': 'America/Los_Angeles'},
                        'end': {'dateTime': interval_end.isoformat(), 'timeZone': 'America/Los_Angeles'},
                    }
                    
                    stage_time_min = (interval_start - timedelta(minutes=1)).isoformat()
                    stage_time_max = (interval_end + timedelta(minutes=1)).isoformat()
                    existing_stage_events = self.service.events().list(
                        calendarId=self.calendar_id,
                        timeMin=stage_time_min,
                        timeMax=stage_time_max,
                        singleEvents=True
                    ).execute()
                    
                    stage_exists = False
                    for existing in existing_stage_events.get('items', []):
                        if existing.get('summary', '').startswith(stage_emoji) and stage in existing.get('summary', ''):
                            stage_exists = True
                            break
                    
                    if not stage_exists:
                        try:
                            self.service.events().insert(calendarId=self.calendar_id, body=stage_event).execute()
                            count += 1
                        except HttpError as e:
                            print(f"Error inserting stage event ({stage}): {e}", file=sys.stderr)
                
            except Exception as e:
                print(f"Skip session: {e}", file=sys.stderr)
                continue
        
        return count
