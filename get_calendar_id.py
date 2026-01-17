#!/usr/bin/env python3
"""Get the Sleep Data calendar ID."""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Get credentials path from env or default
credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'service-account.json')

if not os.path.exists(credentials_path):
    print(f"❌ Credentials not found at {credentials_path}")
    print("Set GOOGLE_CALENDAR_CREDENTIALS_PATH or place service-account.json in current directory")
    exit(1)

creds = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# List all calendars
calendars = service.calendarList().list().execute()

print("\n📅 Available Calendars:\n")
for cal in calendars.get('items', []):
    summary = cal.get('summary', 'Unnamed')
    cal_id = cal.get('id', 'Unknown')
    access_role = cal.get('accessRole', 'Unknown')
    
    if 'Sleep' in summary or 'sleep' in summary.lower():
        print(f"✅ FOUND: {summary}")
        print(f"   Calendar ID: {cal_id}")
        print(f"   Access Role: {access_role}")
        print(f"\n🔗 Add to Google Calendar:")
        print(f"   https://calendar.google.com/calendar/u/0?cid={cal_id}")
        print(f"\n📥 iCal subscription link:")
        print(f"   https://calendar.google.com/calendar/ical/{cal_id}/public/basic.ics")
    else:
        print(f"   {summary}: {cal_id}")
