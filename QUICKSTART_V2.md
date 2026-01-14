# 🚀 Quick Start Guide - Virginia Bill Tracker

## Setup in 10 Minutes (With Web-Based Configuration!)

### What You'll Get:
- ✅ Automated daily bill tracking
- ✅ Beautiful dashboard
- ✅ **Web interface to add/remove bills** (no coding required!)
- ✅ 100% free hosting on GitHub

---

## Step 1: Create GitHub Account
If you don't have one: https://github.com/signup (it's free!)

---

## Step 2: Create New Repository

1. Go to: https://github.com/new
2. **Repository name:** `virginia-bill-tracker`
3. **Description:** "Automated Virginia legislative bill tracker"
4. **Visibility:** ✅ **Public** (required for free features)
5. ✅ Check **"Add a README file"**
6. Click **"Create repository"**

---

## Step 3: Upload Files

### Option A: Web Upload (Easiest)

1. **Download all files** from this folder to your computer

2. **In your new repository**, click **"Add file"** → **"Upload files"**

3. **Drag and drop** ALL files:
   - `track_bills.py` (rename to `track_bills.py`)
   - `.github/workflows/track-bills-v2.yml` (keep in `.github/workflows/` folder)
   - `bills_to_track.json`
   - `scraper_improved.py`
   - `requirements.txt`
   - `README.md`
   - `GH_PAGES_SETUP.md`
   - `setup_gh_pages.sh`

4. **Commit message:** "Initial setup"
5. Click **"Commit changes"**

**Important:** Make sure the `.github` folder structure is preserved:
```
.github/
  workflows/
    track-bills-v2.yml
```

### Option B: Git Command Line

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/virginia-bill-tracker.git
cd virginia-bill-tracker

# Copy all downloaded files to this directory

# Rename files
mv track_bills_v2.py track_bills.py
mv .github/workflows/track-bills-v2.yml .github/workflows/track-bills.yml

# Commit and push
git add .
git commit -m "Initial setup"
git push
```

---

## Step 4: Initial Bill Configuration

**You can do this now OR later via web interface!**

### Option A: Edit Now (Quick Start)

1. In your repository, click **`bills_to_track.json`**
2. Click the **pencil icon** (Edit)
3. Add some bills to get started:

```json
{
  "bills": [
    "HB1",
    "HB7"
  ],
  "settings": {
    "notification_email": null,
    "sync_frequency": "daily",
    "timezone": "America/New_York"
  }
}
```

4. Click **"Commit changes"**

### Option B: Skip for Now
- You can add bills later via the web interface
- The tracker will just show "No bills tracked" until you add some

**Finding Bill IDs:**
- Go to https://lis.virginia.gov/bill-search
- Search for bills you want to track
- Note their ID (e.g., HB1, SB200, HJR5)

---

## Step 5: Run First Sync (Creates gh-pages)

**This step is CRITICAL - it creates the gh-pages branch automatically!**

1. Go to **Actions** tab in your repository
2. Click **"Track Virginia Bills"** on the left
3. Click **"Run workflow"** button (right side)
4. Select branch: **main**
5. Click green **"Run workflow"** button
6. **Wait 1-2 minutes** - watch it run!

You should see:
- ✅ Green checkmark when done
- A message about dashboard being created

**What just happened:**
- Script ran and fetched bill data
- Generated your dashboard HTML
- **Created gh-pages branch automatically**
- Pushed dashboard to gh-pages

---

## Step 6: Enable GitHub Pages

**Now that gh-pages exists, we can enable Pages:**

1. Click **Settings** tab (top of repository)
2. Click **Pages** in left sidebar
3. Under "Build and deployment":
   - **Source:** Deploy from a branch
   - **Branch:** Select **`gh-pages`** (should now be in dropdown!)
   - **Folder:** `/ (root)`
4. Click **Save**

You'll see a message:
```
✓ Your site is ready to be published at https://YOUR-USERNAME.github.io/virginia-bill-tracker/
```

---

## Step 7: View Your Dashboard

**Wait 1-2 minutes** for GitHub to deploy, then visit:

```
https://YOUR-USERNAME.github.io/virginia-bill-tracker/
```

Replace `YOUR-USERNAME` with your GitHub username.

You should see:
- 🏛️ Virginia Bill Tracker header
- Last sync time
- Bills you're tracking (or "No bills tracked")
- **⚙️ Configure Bills button** ← This is important!

---

## Step 8: Configure Bills via Web Interface 🎉

**This is the NEW feature - no more editing JSON files!**

1. **On your dashboard**, click **"⚙️ Configure Bills"**

2. **Get a GitHub Token** (one-time setup):
   - Click the link in the modal: "Create one at GitHub Settings"
   - Or go to: https://github.com/settings/tokens/new
   - **Description:** "Virginia Bill Tracker"
   - **Expiration:** 90 days (or No expiration)
   - **Scopes:** Check ✅ **repo** (full control of private repositories)
   - Scroll down, click **"Generate token"**
   - **Copy the token** (starts with `ghp_...`)
   - **Paste it** in the dashboard's "GitHub Personal Access Token" field

3. **Add Bills:**
   - Type bill ID in the box (e.g., `HB50`)
   - Click **"Add Bill"**
   - Repeat for each bill you want to track

4. **Remove Bills:**
   - Click the **×** next to any bill to remove it

5. **Save Changes:**
   - Click **"💾 Save Changes"**
   - Wait for "✅ Configuration saved!" message

**That's it!** Your bills are now configured and will sync automatically.

---

## 🎉 You're Done!

### What Happens Next?

**Automatic Daily Updates:**
- Every day at **8:00 AM ET**, the tracker runs automatically
- Fetches current status for all your bills
- Detects any changes
- Updates your dashboard
- Highlights bills that changed with an **"UPDATED"** badge

**Manual Updates:**
- Go to Actions → Run workflow anytime
- Or add/remove bills via web interface

**Viewing Your Dashboard:**
- Bookmark: `https://YOUR-USERNAME.github.io/virginia-bill-tracker/`
- Check anytime to see current bill status
- Share the link with colleagues!

---

## 📱 Using the Dashboard

### Main Features:

1. **Bill Cards** - Shows each bill with:
   - Bill number (HB1, SB200, etc.)
   - Current status (In Committee, Passed, etc.)
   - Summary of what the bill does
   - Link to view full details on Virginia LIS

2. **Updated Badges** - Bills with recent changes show "UPDATED"

3. **Change Banner** - Top banner shows if any bills changed

4. **Recent Changes** - Bottom section lists recent status changes

5. **Configure Bills Button** - Manage your tracked bills

### Adding More Bills:

**Method 1: Web Interface (Recommended)**
- Click "Configure Bills"
- Add bills one by one
- Save changes

**Method 2: Edit JSON File**
- Go to repository on GitHub
- Click `bills_to_track.json`
- Edit → Add bills → Commit

---

## 🔧 Customization

### Change Sync Schedule

Edit `.github/workflows/track-bills.yml`:

```yaml
schedule:
  - cron: '0 13 * * *'  # Daily at 8 AM ET
```

**Common schedules:**
- `0 9 * * *` - Daily at 4 AM ET
- `0 9,17 * * *` - Twice daily: 4 AM and 12 PM ET
- `0 13 * * 1-5` - Weekdays only at 8 AM ET

### Add Email Notifications

1. Get an app password from your email provider
2. Add secrets in GitHub: Settings → Secrets → Actions
   - `EMAIL_ADDRESS`
   - `EMAIL_PASSWORD`
3. Modify `track_bills.py` to send emails (see README for code)

---

## 🐛 Troubleshooting

### Dashboard shows 404

**Possible fixes:**
- Wait 2-3 minutes after enabling Pages
- Check: Settings → Pages → Should say "Your site is published"
- Verify `gh-pages` branch exists (code dropdown → branches)
- Repository must be **Public**

### "gh-pages" not in branch dropdown

**Solution:**
- Run the workflow once first (Step 5)
- This creates the branch automatically
- Then enable Pages

### Workflow fails

**Check:**
1. Settings → Actions → General → Workflow permissions
2. Must be set to **"Read and write permissions"**
3. Save if changed
4. Re-run workflow

### Bills not showing

**Check:**
- Bill IDs are correct (check https://lis.virginia.gov)
- Format: HB1, SB200 (not "HB 1" or "hb1")
- `bills_to_track.json` is valid JSON
- Workflow ran successfully (green checkmark in Actions)

### "Configure Bills" button doesn't work

**Check:**
1. Token has `repo` scope
2. Token hasn't expired  
3. Repository name in dashboard matches your repo
4. Browser console for errors (F12)

---

## 📚 Additional Resources

- **Full Documentation:** See `README.md`
- **gh-pages Setup Guide:** See `GH_PAGES_SETUP.md`
- **Automated Setup Script:** Run `setup_gh_pages.sh`

---

## ✅ Final Checklist

Before you're done, verify:

- [ ] Repository created and **public**
- [ ] All files uploaded to `main` branch
- [ ] Workflow exists in `.github/workflows/`
- [ ] Ran workflow once (Actions → Run workflow)
- [ ] `gh-pages` branch exists (check branch dropdown)
- [ ] GitHub Pages enabled (Settings → Pages)
- [ ] Dashboard loads at your GitHub Pages URL
- [ ] "Configure Bills" button opens modal
- [ ] Created GitHub token for configuration
- [ ] Added at least one bill to track

---

## 🆘 Need Help?

1. Check **GH_PAGES_SETUP.md** for detailed gh-pages troubleshooting
2. Review workflow logs: Actions → Latest run → Read logs
3. Verify all files are in correct locations
4. Open an issue in your repository

---

## 🎯 Next Steps

Now that you're set up:

✅ **Add all bills you want to track** (via web interface)
✅ **Bookmark your dashboard**
✅ **Share with colleagues**
✅ **Star your repository** for notifications
✅ **Set your GitHub token expiration reminder**

**Your dashboard will now update automatically every day!** 🎉

---

**Made with ❤️ for Virginia civic engagement**
