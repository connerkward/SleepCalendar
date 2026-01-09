#!/usr/bin/env python3
"""Sync Apple Health sleep data to Google Calendar."""

import os
import sys
import argparse
from pathlib import Path
from apple_health_parser import AppleHealthParser
from healthkit_json_parser import HealthKitJSONParser
from sleep_analyzer import SleepAnalyzer
from calendar_manager import CalendarManager


def main():
    parser = argparse.ArgumentParser(description="Sync sleep data to Google Calendar")
    parser.add_argument("--export-file", type=str, help="Path to export.xml or export.json")
    parser.add_argument("--days", type=int, default=30, help="Days to sync (default: 30)")
    args = parser.parse_args()
    
    # Load config from environment
    credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "service-account.json")
    share_emails = [e.strip() for e in os.getenv("SHARE_WITH_EMAILS", "").split(",") if e.strip()]
    
    # Find export file
    export_file = args.export_file
    if not export_file:
        if Path("export.json").exists():
            export_file = "export.json"
        elif Path("export.xml").exists():
            export_file = "export.xml"
        else:
            print("❌ No export file found. Provide --export-file or place export.xml/export.json in directory")
            sys.exit(1)
    
    print(f"📁 Using: {export_file}")
    
    # Parse sleep data
    file_ext = Path(export_file).suffix.lower()
    if file_ext == ".json":
        parser_obj = HealthKitJSONParser(export_file)
    else:
        parser_obj = AppleHealthParser(export_file)
    
    all_entries = parser_obj.parse()
    iphone_entries = parser_obj.get_iphone_entries(all_entries)
    withings_entries = parser_obj.get_withings_entries(all_entries)
    
    print(f"📊 Found {len(all_entries)} total entries")
    print(f"   iPhone: {len(iphone_entries)}")
    print(f"   Withings: {len(withings_entries)}")
    
    # Merge entries
    analyzer = SleepAnalyzer()
    merged_entries = analyzer.merge_entries(iphone_entries, withings_entries)
    print(f"   Merged: {len(merged_entries)}")
    
    # Sync to calendar
    calendar_mgr = CalendarManager(credentials_path, share_emails)
    calendar_mgr.authenticate()
    calendar_mgr.ensure_calendars_exist()
    
    if iphone_entries:
        count = calendar_mgr.sync_entries_to_calendar(iphone_entries, calendar_mgr.calendar_id_iphone, args.days)
        print(f"✅ Synced {count} iPhone entries")
    
    if withings_entries:
        count = calendar_mgr.sync_entries_to_calendar(withings_entries, calendar_mgr.calendar_id_withings, args.days)
        print(f"✅ Synced {count} Withings entries")
    
    if merged_entries:
        count = calendar_mgr.sync_entries_to_calendar(merged_entries, calendar_mgr.calendar_id_merged, args.days)
        print(f"✅ Synced {count} merged entries")
    
    print("🎉 Sync complete!")


if __name__ == "__main__":
    main()
