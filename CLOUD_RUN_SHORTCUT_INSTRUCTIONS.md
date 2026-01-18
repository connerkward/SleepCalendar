# iOS Shortcut Setup for Cloud Run API

📱 **Pre-built Shortcut:** [Install from iCloud](https://www.icloud.com/shortcuts/440e470b1c6a462a93fddf04b2b74c87)

## Update Your Shortcut

Replace the GitHub upload section with a direct POST to the Cloud Run API.

## Shortcut Actions

Keep steps 1-8 (HealthKit data collection), then replace GitHub steps:

### Replace Steps 9-17 with:

**Email Input - Best for Automation (Store Once):**

**9. Get File** (Try to read stored email first)
- Get file from: `Shortcuts/sleep-calendar-email.txt`
- Error handling: `Continue on Error`

**10. If** (Check if file exists/email was loaded)
- Condition: [File from step 9] is not empty
- **If True (email found):**
  - Use email from file (skip to step 12)
- **If False (file doesn't exist - first run):**
  - **Ask for Input** (step 11)
    - Input Type: `Text`
    - Prompt: `Enter your email address:`
    - Allow Multiple Lines: `No`
    - Default Answer: (leave empty)
  - **Save to File**
    - Save: [Email from Ask for Input]
    - Save to: `Shortcuts/` folder
    - File Name: `sleep-calendar-email.txt`
    - Overwrite: `Always`

**12. Dictionary**
- `email`: [File content from step 9 OR Ask for Input result from step 10]
- `samples`: [Repeat Results]
- **Important:** `samples` must be "Repeat Results" from the repeat loop (keeps it as a list)

**13. Get Contents of URL**
- Method: `POST`
- URL: `https://sleep-calendar-api-939375067398.us-central1.run.app/sync`
- Headers:
  - `Content-Type`: `application/json`
- **Request Body Type: `JSON`** (NOT Text or File!)
- Request Body: [Dictionary from step 12] (pass Dictionary directly, don't convert to Text)
- **No Base64 encoding needed!** The dictionary is sent directly as JSON

**⚠️ Common Error:** If you get "input should be valid list":
- Remove any "Text" action between Dictionary and Get Contents of URL
- Make sure Request Body Type is set to "JSON" (not "Text" or "File")
- Ensure `samples` in Dictionary is "Repeat Results" (not converted to text)

**14. Get Dictionary from Input**
- Input: [URL Response from step 13]
- *Extracts calendar_url from API response*

**15. Get Value for Key**
- Dictionary: [Dictionary from step 14]
- Key: `calendar_url`
- *Gets the calendar URL from the response*

**16. Show Notification** (Recommended for daily automation)
- Title: "✅ Sleep data synced"
- Body: [calendar_url from step 15]
- *Non-intrusive for daily automation. Calendar URL visible for copying if needed.*

**OR for manual runs (if you want auto-open):**

**16. Open URLs** (Alternative - Opens automatically)
- URLs: [calendar_url from step 15]
- *Opens calendar automatically. Only use for manual runs, not automation.*

**17. Show Notification**
- "✅ Sleep data synced. Calendar opened."

## Differences from GitHub Version

| Old (GitHub) | New (Cloud Run) |
|---|---|
| Base64 encode | ❌ **NOT NEEDED** - Send JSON directly |
| Timestamp filename | ❌ Not needed |
| GitHub token | ❌ Not needed |
| PUT method | POST method |
| File path in URL | Endpoint URL |
| Message/content dict | Email/samples dict (direct JSON) |

**Important:** The Cloud Run API accepts JSON directly. No Base64 encoding is required or used.

## Example Request Body

```json
{
  "email": "user@example.com",
  "samples": [
    {
      "startDate": "2026-01-17T02:56:00",
      "endDate": "2026-01-17T03:21:00",
      "value": "Core",
      "sourceName": "Apple Health"
    }
  ]
}
```

## Benefits

- ✅ No GitHub token needed
- ✅ No file management
- ✅ Immediate sync (no GitHub Action delay)
- ✅ Simpler shortcut (no Base64, no timestamps)
- ✅ Automatic per-user calendar creation

## Getting Your Calendar Link

The API returns a `calendar_url` in the response. You can:

**Option 1: Open Automatically**
- Use "Open URLs" action after sync
- Calendar opens directly in Google Calendar app

**Option 2: Copy to Clipboard**
- Use "Copy to Clipboard" action
- Share the link or add to contacts

**Option 3: Show in Notification**
- Extract `calendar_url` from response
- Display in notification or alert

**Example Response:**
```json
{
  "success": true,
  "events_synced": 13,
  "calendar_id": "...@group.calendar.google.com",
  "calendar_url": "https://calendar.google.com/calendar/embed?src=...",
  "error": null
}
```

**Permanent Calendar Link:**
Your calendar is always accessible at:
`https://calendar.google.com/calendar/embed?src={calendar_id}`

The `calendar_id` is returned in every sync response.

## Testing

After updating:
1. Run shortcut manually
2. Check Google Calendar for "Sleep Data - {email}" calendar
3. Verify events are created
4. Note the calendar_url in the response (or open it automatically)

## API Endpoint

**Sync Endpoint:**
```
POST https://sleep-calendar-api-939375067398.us-central1.run.app/sync
```

**Health Check:**
```
GET https://sleep-calendar-api-939375067398.us-central1.run.app/health
```

## Rate Limits

- 30 requests per minute per IP
- 500 requests per hour per IP
- Health endpoints excluded

## Best UX for Daily Automation

For shortcuts that run automatically (e.g., daily at 4 AM):

**Recommended: Notification Only**
- Show notification with calendar URL in body
- Non-intrusive, won't interrupt sleep
- URL visible for copying if user wants it
- No auto-open action (would wake phone)

**Manual Runs:**
- Can add "Open URLs" for immediate access
- Good for testing or when user actively runs shortcut

**Best Practice:** Notification-only for automation, auto-open for manual runs.

## Email Input Options

### Option 1: Store Once (⭐ Recommended for Daily Automation)
**Best UX for automation:**
1. **First run:** "Get File" fails → "Ask for Input" → Save to file (`Shortcuts/sleep-calendar-email.txt`)
2. **Future runs:** "Get File" succeeds → Use email silently (no prompts!)

**Shortcut Flow:**
- Try "Get File" (`Shortcuts/sleep-calendar-email.txt`)
- If file exists: Use email from file (silent, no prompt)
- If file missing: Ask for input, save to file (first run only)

**Benefits:**
- ✅ No prompts during daily automation
- ✅ Works silently at 4 AM
- ✅ User enters email once, never again
- ✅ Perfect for automation

### Option 2: Always Ask (Simple but interrupts automation)
- "Ask for Input" action before Dictionary
- User enters email every time
- ⚠️ **Not recommended for automation** (interrupts at 4 AM)
- Good for testing only

### Option 3: Hardcode (Personal use only)
- Set email as text constant in shortcut
- Only works if distributing to yourself
- Can't distribute to others

**Best Practice:** Option 1 - Store once, reuse silently. Perfect for daily automation.

## Troubleshooting

**429 Too Many Requests:** Rate limit exceeded, wait 1 minute

**500 Error:** Check service account credentials or calendar permissions

**No calendar created:** Verify email format and service account has Calendar API access
