# Sleep Calendar

Auto-sync Apple Health sleep data → Google Calendar with scores (😴 🟢 🔴)

## Mac Setup (Recommended)

Your Mac syncs Health data from iPhone via iCloud. Use this instead of iOS Shortcuts:

**Option 1: launchd (Native macOS)**
```bash
./setup_cron.sh        # Sets up macOS native scheduler
./auto_export_mac.sh   # Test now
```

**Option 2: Mac Shortcuts App (Most Apple-like)**
```bash
./setup_mac_shortcut.sh  # Shows instructions for Shortcuts app
```

**Done!** Runs daily at 4 AM automatically. No iPhone configuration needed.

## What It Does

1. Mac exports Health data (via AppleScript)
2. Uploads to GitHub (via Python)
3. GitHub Action syncs to Google Calendar
4. Calendars shared with email1@example.com, email2@example.com

## Manual Run

```bash
python3 sync_sleep_calendar.py --export-file export.xml
```
