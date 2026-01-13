# 🏛️ Virginia Bill Tracker

**Automated daily monitoring of Virginia legislative bills with change detection and visual dashboard**

Track specific Virginia bills automatically. Get notified when their status changes. View a beautiful dashboard showing current status and recent updates.

## ✨ Features

- ✅ **Track specific bills** by ID (e.g., HB1, SB200)
- 🔄 **Daily automatic updates** via GitHub Actions (completely free!)
- 🔔 **Change detection** - highlights bills with status updates
- 📊 **Live dashboard** hosted on GitHub Pages
- ⏰ **Last sync timestamp** showing when data was last updated
- 📜 **Change history** log of all detected changes
- 🎨 **Beautiful UI** with responsive design
- 💰 **100% Free** - no costs, runs on GitHub infrastructure

## 🚀 Quick Start

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Name it `virginia-bill-tracker` (or any name you prefer)
3. Make it **Public** (required for free GitHub Actions)
4. Check "Add a README file"
5. Click "Create repository"

### 2. Upload Files

Upload these files to your repository:

```
virginia-bill-tracker/
├── .github/
│   └── workflows/
│       └── track-bills.yml          # GitHub Actions workflow
├── data/                             # Created automatically
│   ├── previous_state.json
│   ├── current_state.json
│   └── changes_log.json
├── docs/                             # Created automatically
│   └── index.html
├── track_bills.py                    # Main tracker script
├── scraper.py                        # Web scraper
├── bills_to_track.json              # YOUR CONFIGURATION
└── README.md
```

### 3. Configure Bills to Track

Edit `bills_to_track.json` and add the bills you want to monitor:

```json
{
  "bills": [
    "HB1",
    "HB7",
    "SB200",
    "SB201"
  ],
  "settings": {
    "notification_email": null,
    "sync_frequency": "daily",
    "timezone": "America/New_York"
  }
}
```

**Finding Bill IDs:**
- Go to https://lis.virginia.gov/bill-search
- Search for bills you're interested in
- Note their ID (e.g., "HB1", "SB200")
- Add to the `bills` array in `bills_to_track.json`

### 4. Enable GitHub Pages

1. Go to your repository **Settings**
2. Click **Pages** in the left sidebar
3. Under "Source", select **Deploy from a branch**
4. Select branch: **gh-pages**
5. Click **Save**

Your dashboard will be available at:
`https://YOUR-USERNAME.github.io/virginia-bill-tracker/`

### 5. Run First Sync

**Option A: Manual Trigger**
1. Go to **Actions** tab
2. Click "Track Virginia Bills" workflow
3. Click "Run workflow"
4. Select branch `main`
5. Click "Run workflow"

**Option B: Wait for Automatic Run**
- The tracker runs automatically every day at 8 AM ET
- First run will happen automatically

## 📅 Schedule

By default, the tracker runs:
- **Daily at 8:00 AM ET (1:00 PM UTC)**
- Automatically via GitHub Actions
- Also runs on every push to `main` branch (for testing)

To change the schedule, edit `.github/workflows/track-bills.yml`:

```yaml
schedule:
  - cron: '0 13 * * *'  # Daily at 1 PM UTC (8 AM ET)
```

**Common schedules:**
- `0 13 * * *` - Daily at 8 AM ET
- `0 9,17 * * *` - Twice daily at 4 AM and 12 PM ET
- `0 13 * * 1-5` - Weekdays only at 8 AM ET

## 🎨 Dashboard Features

The auto-generated dashboard shows:

1. **Header**
   - Last sync date and time
   - Total bills tracked

2. **Change Banner**
   - Highlights if any bills have updates
   - Shows count of changes

3. **Bill Cards**
   - Bill number (e.g., HB1)
   - Current status with color coding
   - Bill summary
   - Link to view on Virginia LIS
   - **"UPDATED" badge** for bills that changed

4. **Recent Changes Section**
   - List of recent status changes
   - Timestamp for each change
   - Change details

## 🔧 Customization

### Add More Bills

Edit `bills_to_track.json`:
```json
{
  "bills": [
    "HB1",
    "HB2",
    "HB50",
    "SB1",
    "SB7",
    "SB200"
  ]
}
```

Commit and push. The tracker will pick them up on the next run.

### Change Dashboard Styling

The dashboard HTML is generated in `track_bills.py` in the `generate_dashboard_html()` function. You can customize:
- Colors
- Layout
- Fonts
- Additional information displayed

### Add Email Notifications

You can extend the script to send emails when changes are detected:

1. Add environment secrets in GitHub:
   - `EMAIL_ADDRESS`
   - `EMAIL_PASSWORD`

2. Modify `track_bills.py` to send email when changes detected:

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(changes):
    if not changes:
        return
    
    msg = MIMEText(f"Detected {len(changes)} change(s) in tracked bills")
    msg['Subject'] = 'Virginia Bill Tracker Update'
    msg['From'] = os.environ['EMAIL_ADDRESS']
    msg['To'] = 'your-email@example.com'
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.environ['EMAIL_ADDRESS'], os.environ['EMAIL_PASSWORD'])
        server.send_message(msg)
```

## 📊 Data Files

### `data/current_state.json`
Current status of all tracked bills

### `data/previous_state.json`
Previous status (used for change detection)

### `data/changes_log.json`
Running log of all detected changes (last 1000)

## 🐛 Troubleshooting

### Dashboard Not Updating

1. Check GitHub Actions tab - is the workflow running?
2. Check if gh-pages branch exists
3. Verify GitHub Pages is enabled in Settings

### No Changes Detected

- Ensure bills are correctly formatted (e.g., "HB1" not "hb1" or "H.B. 1")
- Check if bills exist on https://lis.virginia.gov
- View GitHub Actions logs for errors

### Workflow Failing

1. Go to **Actions** tab
2. Click on the failed run
3. Read the error logs
4. Common fixes:
   - Ensure `bills_to_track.json` is valid JSON
   - Check bill IDs are correct
   - Verify GitHub Pages is set up

## 💡 Tips

1. **Test Changes Locally**
   ```bash
   python track_bills.py
   ```

2. **View Generated Dashboard**
   Open `docs/index.html` in your browser

3. **Check What Changed**
   View `data/changes_log.json`

4. **Monitor GitHub Actions**
   Star your repository and enable notifications

## 🔒 Privacy & Data

- All data is stored in your GitHub repository
- Dashboard is publicly accessible (GitHub Pages)
- No external services or databases required
- No personal information collected

## 📈 Scaling

This system can track:
- ✅ Unlimited bills (no limits)
- ✅ Runs daily forever (GitHub Actions free tier)
- ✅ Maintains full history
- ✅ Completely free!

GitHub Actions free tier includes:
- 2,000 minutes/month for private repos
- Unlimited for public repos
- This script uses ~1 minute per run
- = 60 runs/month easily covered

## 🤝 Contributing

Improvements welcome!

Ideas:
- RSS feed generation
- Slack/Discord notifications
- Mobile app integration
- More detailed change tracking
- Export to Excel/CSV
- Historical graphs

## 📜 License

MIT License - feel free to use and modify

## 🆘 Support

Issues? Questions?
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Open an issue on GitHub

---

**Made with ❤️ for Virginia civic engagement**

Track bills. Stay informed. Make a difference.
