# iOS Shortcut Setup

Open Shortcuts app on Mac → Create new → Add:

1. **Find Health Samples** → Sleep Analysis → Last 7 days
2. **Repeat with Each**
   - Get Details: Start Date (ISO 8601)
   - Get Details: End Date (ISO 8601)  
   - Get Details: Source Name
   - Dictionary: startDate, endDate, sourceName
3. **End Repeat**
4. **Get Items from Input**
5. **Dictionary** → Key: samples, Value: items
6. **Make JSON**
7. **Base64 Encode**
8. **Text** → Your GitHub token
9. **Get Contents of URL**
   - PUT to `https://api.github.com/repos/connerkward/SleepCalendar/contents/export.json`
   - Headers: `Authorization: token [token]`
   - Body: JSON with message and base64 content
10. **Show Notification**

Share to iPhone via AirDrop.

Automate: Shortcuts → Automation → Time of Day → 4 AM daily
