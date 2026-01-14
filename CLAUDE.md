# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Virginia Bill Tracker is an automated system that monitors Virginia legislative bills from the Virginia LIS (Legislative Information System) and displays their status on a GitHub Pages dashboard. The system runs as a GitHub Actions workflow that syncs daily at 8 AM ET.

## Commands

**Run the bill tracker locally:**
```bash
python track_bills.py
```

**Dependencies:** requests, beautifulsoup4, selenium (installed via pip)

## Architecture

### Core Components

1. **`track_bills.py`** - Main script that orchestrates the entire workflow:
   - Reads bill IDs from `bills_to_track.json`
   - Fetches bill data from Virginia LIS CSV files (BILLS.CSV and Summaries.csv from blob storage)
   - Compares current state with previous state to detect changes
   - Generates the HTML dashboard with embedded JavaScript for web-based configuration
   - Saves state to JSON files in `data/`

2. **`.github/workflows/track-bills.yml`** - GitHub Actions workflow that:
   - Runs on schedule (daily at 8 AM ET), manual trigger, or push to main
   - Creates the `gh-pages` branch if it doesn't exist
   - Deploys the dashboard to GitHub Pages using `peaceiris/actions-gh-pages@v3`

### Data Flow

```
bills_to_track.json → track_bills.py → data/*.json + docs/index.html → gh-pages branch → GitHub Pages
```

### Key Files

- `bills_to_track.json` - Configuration file with list of bill IDs to track (editable via web interface or directly)
- `data/current_state.json` - Current bill statuses (updated each run)
- `data/previous_state.json` - Previous run's state (for change detection)
- `data/changes_log.json` - Historical log of all detected changes (keeps last 1000)
- `docs/index.html` - Generated dashboard with embedded configuration UI

### Dashboard Features

The generated HTML dashboard includes:
- Bill cards with status, summary, and LIS links
- Change detection badges ("UPDATED")
- Web-based configuration modal that uses GitHub API to update `bills_to_track.json`
- The modal requires a GitHub Personal Access Token with `repo` scope

### Data Source

Bill data is fetched from Virginia LIS blob storage CSV files:
- URL pattern: `https://lis.blob.core.windows.net/lisfiles/{session}/BILLS.CSV`
- Session format: `20251` = 2025 Regular Session, `20252` = 2025 Special Session
- The `CURRENT_SESSION` constant in `track_bills.py` controls which session to fetch

### Bill ID Format

Valid formats: `HB9`, `SB200`, `HJR5`, `SJR1`, `HR1`, `SR1` (prefix + number, case-insensitive)

Note: Bill numbers vary by session. Not all numbers exist (e.g., HB1 may not exist in a given session).
