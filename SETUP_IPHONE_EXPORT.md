# iPhone Health Export to Mac

Health data cannot be directly exported from macOS. You need to export from iPhone.

## One-Time Manual Export (Weekly/Monthly)

### On iPhone:
1. Open **Health** app
2. Tap **profile icon** (top right)
3. Scroll down → **Export All Health Data**
4. Wait (can take 1-2 minutes)
5. **AirDrop** the ZIP to your Mac
6. **Extract** the ZIP in Downloads folder
7. Keep `export.xml` in Downloads

### On Mac:
```bash
cd ~/Downloads
unzip export.zip  # Creates export.xml
cd /Users/CONWARD/dev/SleepCalendar
./auto_export_mac.sh
```

The Mac script will:
- Find export.xml in Downloads
- Upload to GitHub
- Archive the old export

## Frequency

**Export weekly or monthly from iPhone.** The Mac automation will upload the latest data to GitHub, which syncs to Calendar.

## Alternative: iOS Shortcut (Fully Automated)

If you want **true automation**, you need an iOS Shortcut:
1. Creates daily exports automatically
2. Uploads directly to GitHub
3. No Mac needed

See: https://support.apple.com/guide/shortcuts/welcome/ios

But that requires building the shortcut on iPhone (5 minutes setup).
