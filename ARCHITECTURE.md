# System Architecture - Virginia Bill Tracker

## 📊 Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR WORKFLOW                           │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────────┐
   │  You (The User)  │
   └────────┬─────────┘
            │
            │ 1. Configure Bills
            │    (via web interface)
            ▼
   ┌─────────────────────────┐
   │  Dashboard (Browser)    │
   │  - Add/Remove Bills     │
   │  - Enter GitHub Token   │
   │  - Click "Save"         │
   └────────┬────────────────┘
            │
            │ 2. Updates via GitHub API
            ▼
   ┌─────────────────────────────────┐
   │  GitHub Repository (main)       │
   │  bills_to_track.json UPDATED    │
   └────────┬────────────────────────┘
            │
            │ 3. Triggers workflow
            │    (on schedule OR manual)
            ▼
   ┌─────────────────────────────────┐
   │  GitHub Actions (Cloud Runner)  │
   │  - Runs track_bills.py          │
   │  - Fetches bill data            │
   │  - Detects changes              │
   │  - Generates dashboard          │
   └────────┬────────────────────────┘
            │
            │ 4. Pushes to gh-pages
            ▼
   ┌─────────────────────────────────┐
   │  gh-pages branch                │
   │  - Contains index.html          │
   │  - Auto-updated dashboard       │
   └────────┬────────────────────────┘
            │
            │ 5. Hosts website
            ▼
   ┌─────────────────────────────────┐
   │  GitHub Pages (Public URL)      │
   │  https://username.github.io/... │
   └────────┬────────────────────────┘
            │
            │ 6. You view dashboard
            ▼
   ┌──────────────────┐
   │  You (The User)  │
   │  See bill status │
   └──────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────────┐
│ Virginia LIS │  ← Official source of bill data
│  Website     │     (lis.virginia.gov)
└──────┬───────┘
       │
       │ Scrapes data
       │ (during sync)
       ▼
┌─────────────────────────┐
│  track_bills.py         │
│  1. Reads config        │
│  2. Fetches bills       │
│  3. Compares with old   │
│  4. Detects changes     │
│  5. Generates HTML      │
└──────┬──────────────────┘
       │
       │ Writes to
       ▼
┌─────────────────┐     ┌─────────────────┐
│ data/           │     │ docs/           │
│ - current.json  │     │ - index.html    │
│ - previous.json │     │   (dashboard)   │
│ - changes.json  │     └─────────────────┘
└─────────────────┘            │
       │                       │
       │                       │ Deployed to
       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ main branch     │     │ gh-pages branch │
│ (source code)   │     │ (website only)  │
└─────────────────┘     └─────────────────┘
```

---

## 🗂️ Repository Structure

### Main Branch (`main`)
```
virginia-bill-tracker/
│
├── .github/
│   └── workflows/
│       └── track-bills.yml       ← Automation config
│
├── data/                         ← Bill tracking data
│   ├── current_state.json        ← Current bill statuses
│   ├── previous_state.json       ← Previous run (for comparison)
│   └── changes_log.json          ← History of all changes
│
├── docs/                         ← Generated dashboard
│   └── index.html                ← Your dashboard (auto-generated)
│
├── track_bills.py                ← Main Python script
├── scraper_improved.py           ← Web scraper for Virginia LIS
├── requirements.txt              ← Python dependencies
│
├── bills_to_track.json           ← 🌟 YOUR CONFIGURATION
│                                    (edited via web interface)
├── README.md                     ← Full documentation
├── QUICKSTART_V2.md             ← This guide
├── GH_PAGES_SETUP.md            ← gh-pages detailed guide
└── setup_gh_pages.sh            ← Automated setup script
```

### GitHub Pages Branch (`gh-pages`)
```
virginia-bill-tracker/ (gh-pages branch)
│
└── index.html                    ← Dashboard (auto-deployed)
                                     Don't edit manually!
```

---

## ⚙️ Configuration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Adding a New Bill                        │
└─────────────────────────────────────────────────────────────┘

Method 1: Web Interface (Recommended)
────────────────────────────────────
1. Open dashboard
2. Click "Configure Bills"
3. Enter GitHub token
4. Type bill ID (e.g., "HB50")
5. Click "Add Bill"
6. Click "Save Changes"
   ↓
   GitHub API updates bills_to_track.json
   ↓
   Next sync will include the new bill


Method 2: Direct Edit
──────────────────────
1. Go to repository on GitHub
2. Click bills_to_track.json
3. Click edit (pencil icon)
4. Add bill to "bills" array
5. Commit changes
   ↓
   File updated in main branch
   ↓
   Next sync will include the new bill


Both methods trigger:
──────────────────────
Next workflow run →
Fetch new bill data →
Update dashboard →
You see the new bill on website
```

---

## 🕐 Sync Schedule

```
┌────────────────────────────────────────┐
│         Daily Sync Process             │
└────────────────────────────────────────┘

8:00 AM ET - GitHub Actions triggers
    ↓
8:00:30 AM - Script starts running
    ├─ Read bills_to_track.json
    ├─ For each bill:
    │   └─ Fetch from Virginia LIS
    ├─ Compare with yesterday's data
    └─ Detect any changes
    ↓
8:01:00 AM - Generate new dashboard
    ├─ Create HTML with current data
    ├─ Highlight changed bills
    └─ Add change history
    ↓
8:01:30 AM - Deploy to gh-pages
    ├─ Push index.html to gh-pages branch
    └─ GitHub Pages auto-deploys
    ↓
8:02:00 AM - Dashboard updated!
    └─ Visit URL to see latest data

Manual Trigger:
───────────────
You can also run anytime:
Actions → Run workflow → Click green button
```

---

## 🔐 Security & Permissions

```
┌──────────────────────────────────────────────────────────┐
│              GitHub Token Permissions                    │
└──────────────────────────────────────────────────────────┘

Your Personal Access Token needs:
✅ repo (Full control of private repositories)
   └─ Allows web interface to update bills_to_track.json

Workflow Permissions (automatic):
✅ contents: write
   └─ Allows Actions to commit data and push to gh-pages

Token Storage:
❌ NEVER stored in code
❌ NEVER committed to repository
✅ Only used during configuration
✅ You enter it each time (or store in password manager)
```

---

## 💾 Data Storage

```
Where is data stored?
─────────────────────

bills_to_track.json (main branch)
├─ Your configuration
├─ List of bill IDs to track
└─ Edited via web interface or directly

data/current_state.json (main branch)
├─ Current status of all bills
├─ Updated after each sync
└─ Used to generate dashboard

data/previous_state.json (main branch)
├─ Status from previous sync
├─ Used for change detection
└─ Automatically managed

data/changes_log.json (main branch)
├─ History of all detected changes
├─ Keeps last 1000 changes
└─ Shown in "Recent Changes" section

docs/index.html (main branch → gh-pages)
├─ Generated dashboard HTML
├─ Created by track_bills.py
└─ Deployed to gh-pages for hosting

All data is in YOUR repository
No external databases
No cloud storage fees
All changes tracked in Git history
```

---

## 🌐 URLs & Endpoints

```
Your Repository:
https://github.com/YOUR-USERNAME/virginia-bill-tracker

Your Dashboard (GitHub Pages):
https://YOUR-USERNAME.github.io/virginia-bill-tracker/

Virginia LIS (Source Data):
https://lis.virginia.gov/bill-search
https://lis.virginia.gov/bill-details/20261/HB1

GitHub API (Used by Web Interface):
https://api.github.com/repos/YOUR-USERNAME/virginia-bill-tracker/contents/bills_to_track.json

GitHub Actions:
https://github.com/YOUR-USERNAME/virginia-bill-tracker/actions
```

---

## 🎯 Quick Reference

```
┌──────────────────────────────────────┐
│      Common Tasks                    │
└──────────────────────────────────────┘

Add a bill:
  → Dashboard → Configure Bills → Add

Remove a bill:
  → Dashboard → Configure Bills → Click ×

Force update:
  → Actions → Run workflow

View history:
  → Dashboard → Recent Changes section

Change schedule:
  → Edit .github/workflows/track-bills.yml

Check logs:
  → Actions → Latest run → Click job name

Troubleshoot:
  → Read GH_PAGES_SETUP.md
```

---

## 📊 Bill Status Legend

```
┌──────────────────────────────────────┐
│     Status Color Coding              │
└──────────────────────────────────────┘

🔵 In Committee
   Blue badge - Bill is being reviewed

🟢 Passed
   Green badge - Bill passed successfully

🔴 Failed
   Red badge - Bill was rejected

🟡 Pending
   Yellow badge - Awaiting action

🟠 UPDATED
   Orange badge - Changed since last sync
```

---

This visual guide should help you understand how everything connects! 🎉
