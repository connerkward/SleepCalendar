# Sleep Calendar

Auto-sync Apple Health sleep data → Google Calendar with scores (😴 🟢 🔴)

## Mac Setup (Recommended)

Your Mac syncs Health data from iPhone via iCloud. Use this instead of iOS Shortcuts:

```bash
# One-time setup
./setup_cron.sh

# Test now
./auto_export_mac.sh
```

**Done!** Runs daily at 4 AM. No iPhone shortcuts needed.

## What It Does

1. Mac exports Health data (via AppleScript)
2. Uploads to GitHub (via Python)
3. GitHub Action syncs to Google Calendar
4. Calendars shared with email1@example.com, email2@example.com

## Manual Run

```bash
python3 sync_sleep_calendar.py --export-file export.xml
```
