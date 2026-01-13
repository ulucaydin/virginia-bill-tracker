# 📘 Complete GitHub Pages (gh-pages) Setup Guide

## What is gh-pages?

`gh-pages` is a special Git branch that GitHub uses to host your website for free. Your bill tracker dashboard will be publicly accessible at:

```
https://YOUR-USERNAME.github.io/virginia-bill-tracker/
```

## Why Do We Need It?

- **Main branch**: Stores your code, scripts, and configuration
- **gh-pages branch**: Hosts only the generated HTML dashboard
- GitHub Actions automatically updates gh-pages after each sync

## 🚀 Setup Methods

### Method 1: Automatic Setup (Recommended)

**This method creates the gh-pages branch automatically on first run**

1. **Upload all files to your repository's main branch**
   - Include all `.py` files, `.yml` workflow, `bills_to_track.json`

2. **Run the workflow manually** (first time only)
   - Go to **Actions** tab in your repository
   - Click "Track Virginia Bills" workflow
   - Click **"Run workflow"** button
   - Select branch: `main`
   - Click green **"Run workflow"**

3. **Wait for it to complete** (1-2 minutes)
   - The workflow will automatically create the `gh-pages` branch
   - It will push your dashboard HTML to that branch

4. **Enable GitHub Pages**
   - Go to **Settings** → **Pages**
   - Source: **Deploy from a branch**
   - Branch: Select **`gh-pages`** (should now appear in dropdown)
   - Folder: **`/ (root)`**
   - Click **Save**

5. **Wait 1-2 minutes**, then visit:
   ```
   https://YOUR-USERNAME.github.io/virginia-bill-tracker/
   ```

---

### Method 2: Manual Branch Creation

**If the automatic method doesn't work, create gh-pages manually:**

#### Option A: Using GitHub Website

1. **Go to your repository on GitHub**

2. **Click the branch dropdown** (shows "main" by default)

3. **Type `gh-pages` in the "Find or create a branch" box**

4. **Click "Create branch: gh-pages from main"**

5. **Go to Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: **`gh-pages`**
   - Click **Save**

6. **Run the workflow** to populate the branch with dashboard

#### Option B: Using Git Command Line

```bash
# Clone your repository
git clone https://github.com/YOUR-USERNAME/virginia-bill-tracker.git
cd virginia-bill-tracker

# Create empty gh-pages branch
git checkout --orphan gh-pages

# Remove all files from this branch
git rm -rf .

# Create a placeholder index.html
echo "<h1>Bill Tracker Dashboard</h1><p>Waiting for first sync...</p>" > index.html

# Commit and push
git add index.html
git commit -m "Initialize gh-pages branch"
git push origin gh-pages

# Switch back to main
git checkout main
```

7. **Enable GitHub Pages** (Settings → Pages → gh-pages branch)

8. **Run the workflow** to generate the real dashboard

---

### Method 3: Using Setup Script

I've created a script that does everything for you:

```bash
# Download the setup script
curl -o setup_gh_pages.sh https://raw.githubusercontent.com/YOUR-USERNAME/virginia-bill-tracker/main/setup_gh_pages.sh

# Make it executable
chmod +x setup_gh_pages.sh

# Run it
./setup_gh_pages.sh
```

---

## 🔍 Verify Setup

### Check if gh-pages branch exists:

1. Go to your repository on GitHub
2. Click the branch dropdown (top left, near the file list)
3. You should see both `main` and `gh-pages`

### Check if GitHub Pages is enabled:

1. Go to **Settings** → **Pages**
2. You should see: "Your site is published at https://..."
3. The source should show: **Branch: gh-pages**

### Check if dashboard is live:

Visit: `https://YOUR-USERNAME.github.io/virginia-bill-tracker/`

- If you see the dashboard → ✅ Everything works!
- If you see 404 → Wait 1-2 minutes and refresh
- If still 404 → Check troubleshooting below

---

## 🎯 How It All Works Together

```
┌─────────────────────────────────────────────────┐
│  1. You edit bills_to_track.json on main branch │
│     (via web interface or directly)             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  2. GitHub Actions runs daily (or manually)     │
│     - Fetches bill data from Virginia LIS       │
│     - Detects changes                           │
│     - Generates dashboard HTML                  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  3. Workflow pushes dashboard to gh-pages       │
│     - Only the HTML file (docs/index.html)      │
│     - This branch is for hosting only           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  4. GitHub Pages serves the website             │
│     from gh-pages branch at your URL            │
└─────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Problem: "gh-pages" doesn't appear in branch dropdown

**Solution:**
- Run the workflow once (Actions → Run workflow)
- Or create it manually using Method 2

### Problem: 404 when visiting dashboard URL

**Possible causes:**

1. **GitHub Pages not enabled**
   - Go to Settings → Pages
   - Set Source to "gh-pages" branch

2. **gh-pages branch is empty**
   - Check if branch exists (code dropdown)
   - Run workflow to populate it

3. **Wrong URL**
   - Should be: `https://USERNAME.github.io/REPO-NAME/`
   - Not: `https://github.com/USERNAME/REPO-NAME/`

4. **Repository is private**
   - GitHub Pages requires public repository for free hosting
   - Go to Settings → Danger Zone → Change visibility → Public

5. **Just enabled - needs time**
   - Wait 2-3 minutes after enabling
   - Clear browser cache and retry

### Problem: Workflow fails with "gh-pages not found"

**Solution:**
Create the branch first using Method 2, then run workflow

### Problem: Dashboard shows old data

**Possible causes:**

1. **Browser cache**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

2. **Workflow didn't run**
   - Check Actions tab for recent runs
   - Manually trigger: Actions → Run workflow

3. **Workflow failed**
   - Click on failed workflow run in Actions
   - Read error logs
   - Usually permission issues or branch problems

---

## 🔒 Permissions

### Required GitHub Permissions:

The workflow needs permission to:
- ✅ Read your repository code
- ✅ Write to gh-pages branch
- ✅ Read/write repository contents

These are set in `.github/workflows/track-bills.yml`:

```yaml
permissions:
  contents: write
```

If workflow fails with permission errors:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to "Workflow permissions"
3. Select **"Read and write permissions"**
4. Click **Save**

---

## 📊 What's Stored Where?

### Main Branch (`main`):
```
virginia-bill-tracker/
├── .github/workflows/     # GitHub Actions automation
├── data/                  # Bill tracking data
├── track_bills.py         # Main script
├── bills_to_track.json    # YOUR CONFIGURATION ⭐
└── other files...
```

### GitHub Pages Branch (`gh-pages`):
```
virginia-bill-tracker/ (gh-pages branch)
└── index.html            # Your dashboard (auto-generated)
```

**Note:** You should NEVER manually edit files in gh-pages branch. They're auto-generated!

---

## 🎓 Advanced: Custom Domain

Want to use your own domain instead of github.io?

1. **Get a domain** (e.g., from Namecheap, Google Domains)

2. **Add CNAME record** in your domain settings:
   ```
   Type: CNAME
   Name: bills (or @)
   Value: YOUR-USERNAME.github.io
   ```

3. **Configure in GitHub:**
   - Settings → Pages
   - Custom domain: `bills.yourdomain.com`
   - Save

4. **Enable HTTPS** (recommended):
   - Wait for DNS to propagate (few hours)
   - Check "Enforce HTTPS"

---

## 🔄 Updating Your Dashboard

The dashboard updates automatically, but if you want to force an update:

### Method 1: Manual Workflow Trigger
1. Go to **Actions** tab
2. Click "Track Virginia Bills"
3. Click **"Run workflow"**
4. Click green **"Run workflow"** button

### Method 2: Push to Main
```bash
# Make any change to main branch
git commit --allow-empty -m "Trigger workflow"
git push
```

### Method 3: Wait for Schedule
- Automatically runs daily at 8 AM ET
- No action needed!

---

## 📝 Summary Checklist

- [ ] Repository created and public
- [ ] All files uploaded to main branch
- [ ] Workflow file in `.github/workflows/`
- [ ] `bills_to_track.json` configured with your bills
- [ ] Workflow run at least once
- [ ] `gh-pages` branch exists
- [ ] GitHub Pages enabled (Settings → Pages)
- [ ] Source set to `gh-pages` branch
- [ ] Dashboard accessible at `https://USERNAME.github.io/REPO-NAME/`
- [ ] "Configure Bills" button works on dashboard

---

## 🆘 Still Having Issues?

1. **Check workflow logs:** Actions tab → Latest run → Click on job → Read logs
2. **Verify branch exists:** Code dropdown → See branches
3. **Check Pages status:** Settings → Pages → Look for green checkmark
4. **Repository public?** Settings → Check visibility
5. **Wait a bit:** Sometimes takes 2-3 minutes for changes to propagate

---

**Need more help?** Open an issue in your repository with:
- What you tried
- Error messages
- Screenshots of Settings → Pages

The community can help debug! 🚀
