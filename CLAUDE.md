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
   - Fetches bill data from Virginia LIS (via placeholder implementation)
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

### Bill ID Format

Valid formats: `HB1`, `SB200`, `HJR5`, `SJR1`, `HR1`, `SR1` (prefix + number, case-insensitive)
