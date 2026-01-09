# Sleep Calendar

Auto-sync Apple Health sleep data → Google Calendar with scores (😴 🟢 🔴)

## Setup

**Health data must be exported from iPhone** (no direct Mac export exists).

### Option 1: Manual Export (Simplest)

1. **Export from iPhone** (weekly/monthly):
   - Health app → Profile → Export All Health Data
   - AirDrop ZIP to Mac → Extract to Downloads
   
2. **Upload from Mac**:
   ```bash
   ./auto_export_mac.sh
   ```

See `SETUP_IPHONE_EXPORT.md` for detailed steps.

### Option 2: Automate with launchd (after manual export)

```bash
./setup_cron.sh        # Checks Downloads daily
./auto_export_mac.sh   # Test now
```

This checks for updated exports and uploads to GitHub.

### Option 3: iOS Shortcut (Fully Automated)

Build iOS Shortcut once, runs daily automatically. See iOS Shortcuts documentation.

## What It Does

1. Mac exports Health data (via AppleScript)
2. Uploads to GitHub (via Python)
3. GitHub Action syncs to Google Calendar
4. Calendars shared with email1@example.com, email2@example.com

## Manual Run

```bash
python3 sync_sleep_calendar.py --export-file export.xml
```
