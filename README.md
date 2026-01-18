# Sleep Calendar

Auto-sync iPhone sleep data to Google Calendar with scores (😴 🟢 🔴)

📱 **Get the Shortcut:** [Install from iCloud](https://www.icloud.com/shortcuts/440e470b1c6a462a93fddf04b2b74c87)

## Quick Start

1. **Install the shortcut** using the link above
2. **Run the shortcut** - it will prompt for your email on first run
3. **Get your calendar link** from the notification or response
4. **Subscribe to the calendar** in Google Calendar

## How to Use

### First Run

1. Run the shortcut manually
2. Enter your email address when prompted (it will be saved for future runs)
3. The shortcut will sync your sleep data and show your calendar link

### Daily Automation

1. Open **Shortcuts** app → **Automation** tab
2. **Create Personal Automation** → **Time of Day**
3. Set time (e.g., `4:00 AM`) → **Daily**
4. **Run Shortcut** → Select "Sleep Calendar"
5. Turn off **"Ask Before Running"**

The shortcut runs automatically and syncs your sleep data daily.

### Adding Calendar to Google Calendar

1. Copy the calendar link from the notification (or API response)
2. Open Google Calendar
3. Click **+** next to "Other calendars"
4. **From URL** → Paste the calendar link
5. Click **Add calendar**

Your calendar is publicly readable, so anyone can subscribe using the link.

## Sleep Scores

Each sleep event is scored 0-100 based on duration:

- **🟢 70-100**: Good sleep (7-8 hours ideal)
- **😴 50-69**: Fair sleep (6-7 hours)
- **🔴 0-49**: Poor sleep (<6 hours or >10 hours)

### Scoring Details

- **< 6 hours**: Score = (duration/6) × 50 (0-50 range)
- **6-8 hours**: Score = 50 + (duration - 6)/2 × 50 (50-100 range, peak at 8h)
- **8-10 hours**: Score = 100 - (duration - 8)/2 × 10 (100-90 range)
- **> 10 hours**: Score = max(0, 100 - (duration - 10) × 20)

Scores are shown in the event title (emoji) and description (full score with breakdown).

## Features

- ✅ Automatic daily sync
- ✅ Per-user calendars (one per email)
- ✅ Detailed sleep stage events (Core, Deep, REM, Awake)
- ✅ Aggregated sleep sessions
- ✅ Public calendar links for easy subscription

## How It Works

1. Shortcut collects sleep data from Apple Health (last 7 days)
2. Sends data to API with your email
3. API creates/updates your personal calendar: `Sleep Data - {email}`
4. Calendar is publicly readable (anyone can subscribe via link)

## For Developers

This project uses a Cloud Run API to handle calendar creation and syncing. See the codebase for implementation details.

- [CLOUD_RUN_SETUP.md](CLOUD_RUN_SETUP.md) - Deployment guide
- [CLOUD_RUN_SHORTCUT_INSTRUCTIONS.md](CLOUD_RUN_SHORTCUT_INSTRUCTIONS.md) - Shortcut customization

## License

MIT
