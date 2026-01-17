# Sleep Calendar

Auto-sync iPhone sleep data to Google Calendar with scores (😴 🟢 🔴)

## Setup (One Time)

### 1. Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Add GitHub Secrets

1. Go to: `https://github.com/YOUR_USERNAME/SleepCalendar/settings/secrets/actions`
2. Add these secrets:
   
   **GOOGLE_CALENDAR_CREDENTIALS**
   - Click "New repository secret"
   - Name: `GOOGLE_CALENDAR_CREDENTIALS`
   - Value: Paste entire contents of `service-account.json`
   - Click "Add secret"
   
   **SHARE_WITH_EMAILS** (optional)
   - Click "New repository secret"
   - Name: `SHARE_WITH_EMAILS`
   - Value: `email1@example.com,email2@example.com` (comma-separated)
   - Click "Add secret"

### 3. Create iOS Shortcut

Open **Shortcuts app on iPhone** → Create new shortcut → Add these actions:

#### Actions:

1. **Find Health Samples**
   - Type: `Sleep` (select from the list)
   - Date: `Last 7 Days`

2. **Repeat with Each** (item = Health Sample)

3. **Get Details of Health Sample**
   - Detail: `Start Date`
   - Format: `ISO 8601`

4. **Get Details of Health Sample**
   - Detail: `End Date`
   - Format: `ISO 8601`

5. **Get Details of Health Sample**
   - Detail: `Source Name`

6. **Dictionary**
   - `startDate`: [Start Date from step 3]
   - `endDate`: [End Date from step 4]
   - `sourceName`: [Source Name from step 5]

7. **End Repeat**

8. **Dictionary**
   - `samples`: [Repeat Results]

9. **Text**
   - Insert the Dictionary variable from step 8 into the text field
   - This converts the dictionary to JSON text format

10. **Base64 Encode**
    - Input: Text from step 9

11. **Text**
    - Content: `YOUR_GITHUB_TOKEN`
    - Generate token: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
    - Required scope: `repo` (full control of private repositories)
    - Copy the token and paste here

12. **Get Contents of URL** (GET existing file to get sha)
    - Method: `GET`
    - URL: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/contents/export.json`
    - Headers:
      - `Authorization`: `token [Text from step 11]`
      - `Accept`: `application/vnd.github.v3+json`

13. **Get Dictionary from Input**
    - Input: Contents of URL from step 12

14. **Get Value for Key**
    - Dictionary: [Dictionary from step 13]
    - Key: `sha`
    - (This extracts the current file's SHA hash)

15. **Dictionary**
    - `message`: `Update sleep data`
    - `content`: [Base64 from step 10]
    - `sha`: [Value from step 14]

16. **Text**
    - Insert Dictionary from step 15 (converts to JSON)

17. **Get Contents of URL** (PUT to update file)
    - Method: `PUT`
    - URL: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/contents/export.json`
    - Headers:
      - `Authorization`: `token [Text from step 11]`
      - `Accept`: `application/vnd.github.v3+json`
      - `Content-Type`: `application/json`
    - Request Body Type: `File`
    - Request Body: [Text from step 16]

18. **Show Notification**
    - "✅ Sleep data uploaded"

**Note:** On the first run (when `export.json` doesn't exist yet), step 12 may fail with a 404. You can either:
- Handle the error gracefully (use "If" action to check for error, then set sha to empty string)
- Or manually create an empty `export.json` file in your repo first

#### Automate:

1. Go to **Shortcuts** → **Automation** tab
2. **Create Personal Automation**
3. **Time of Day** → `4:00 AM` → **Daily**
4. **Run Shortcut** → Select your sleep export shortcut
5. **Turn off** "Ask Before Running"

### 4. Test

Run the shortcut manually once. Check:
- GitHub for `export.json`
- Actions tab for workflow run
- Google Calendar for events

## Done

Runs daily at 4 AM automatically. Zero maintenance.

## Calendar Access

If you set `SHARE_WITH_EMAILS`, those users will have write access to the calendar.

Find in Google Calendar → "Other calendars" → "Sleep Data"
