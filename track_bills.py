#!/usr/bin/env python3
"""
Virginia Legislative Bill Tracker
Fetches bill status and highlights changes
Now includes web-based configuration interface
"""

import json
import requests
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional
import os

# Configuration
BILLS_TO_TRACK_FILE = "bills_to_track.json"
# Virginia LIS data URL - 20261 = 2026 Regular Session
LIS_DATA_BASE_URL = "https://lis.blob.core.windows.net/lisfiles"
CURRENT_SESSION = "20261"
PREVIOUS_STATE_FILE = "data/previous_state.json"
CURRENT_STATE_FILE = "data/current_state.json"
CHANGES_LOG_FILE = "data/changes_log.json"

def load_bills_to_track() -> List[str]:
    """Load the list of bill IDs to track from config file"""
    try:
        with open(BILLS_TO_TRACK_FILE, 'r') as f:
            config = json.load(f)
            return [bill.upper() for bill in config.get('bills', [])]
    except FileNotFoundError:
        print(f"Warning: {BILLS_TO_TRACK_FILE} not found. Using empty list.")
        return []

def fetch_lis_csv(filename: str, session: str = CURRENT_SESSION) -> Optional[List[Dict]]:
    """Fetch and parse a CSV file from Virginia LIS blob storage"""
    url = f"{LIS_DATA_BASE_URL}/{session}/{filename}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse CSV content
        content = response.content.decode('utf-8-sig')  # Handle BOM if present
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    except requests.RequestException as e:
        print(f"Error fetching {filename}: {e}")
        return None


def normalize_bill_id(bill_id: str) -> str:
    """Normalize bill ID to standard format (e.g., HB0009 -> HB9, HB9 -> HB9)"""
    import re
    match = re.match(r'^([A-Z]+)0*(\d+)$', bill_id.upper().strip())
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return bill_id.upper().strip()


def strip_html(text: str) -> str:
    """Remove HTML tags from text"""
    import re
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return clean.strip()


def get_bill_status(bill_row: Dict) -> str:
    """Determine bill status from CSV row data"""
    # Check governor action first
    gov_action = bill_row.get('Last_governor_action', '').strip()
    if gov_action:
        if 'Approved' in gov_action or 'Signed' in gov_action:
            return 'Signed into Law'
        elif 'Vetoed' in gov_action:
            return 'Vetoed'

    # Check if passed both chambers
    passed_house = bill_row.get('Passed_house', '').strip().upper()
    passed_senate = bill_row.get('Passed_senate', '').strip().upper()
    if passed_house == 'Y' and passed_senate == 'Y':
        return 'Passed Both Chambers'
    elif passed_house == 'Y':
        return 'Passed House'
    elif passed_senate == 'Y':
        return 'Passed Senate'

    # Check last action for status clues
    house_action = bill_row.get('Last_house_action', '').strip()
    senate_action = bill_row.get('Last_senate_action', '').strip()
    last_action = house_action or senate_action

    if 'Left in' in last_action:
        return 'Left in Committee'
    elif 'Continued to' in last_action:
        return 'Continued'
    elif 'Failed' in last_action or 'Defeated' in last_action:
        return 'Failed'
    elif 'Committee' in last_action or 'Referred' in last_action:
        return 'In Committee'

    return 'Pending'


def fetch_bill_data(bill_numbers: List[str]) -> Dict:
    """
    Fetch current data for specified bills from Virginia LIS CSV files
    """
    bills_data = {}

    if not bill_numbers:
        return bills_data

    # Fetch bills and summaries CSVs
    print(f"   Fetching data from Virginia LIS (session {CURRENT_SESSION})...")
    bills_csv = fetch_lis_csv("BILLS.CSV")
    summaries_csv = fetch_lis_csv("Summaries.csv")

    if not bills_csv:
        print("   Warning: Could not fetch BILLS.CSV, using fallback data")
        # Return placeholder data if CSV fetch fails
        for bill_num in bill_numbers:
            bills_data[bill_num] = {
                'bill_number': bill_num,
                'bill_url': f"https://lis.virginia.gov/bill-details/{CURRENT_SESSION}/{bill_num}",
                'status': 'Data unavailable',
                'summary': 'Could not fetch bill data from Virginia LIS',
                'last_action': 'Unknown',
                'last_action_date': ''
            }
        return bills_data

    # Build lookup dictionaries - normalize bill IDs
    bills_by_number = {}
    for row in bills_csv:
        bill_id = row.get('Bill_id', '').strip()
        if bill_id:
            normalized = normalize_bill_id(bill_id)
            bills_by_number[normalized] = row

    summaries_by_number = {}
    if summaries_csv:
        for row in summaries_csv:
            # Summaries use SUM_BILNO column with zero-padded IDs (e.g., HB0009)
            bill_id = row.get('SUM_BILNO', '').strip()
            if bill_id:
                normalized = normalize_bill_id(bill_id)
                summary_text = row.get('SUMMARY_TEXT', '').strip()
                # Strip HTML and store
                summaries_by_number[normalized] = strip_html(summary_text)

    # Process requested bills
    for bill_num in bill_numbers:
        bill_num_normalized = normalize_bill_id(bill_num)

        if bill_num_normalized in bills_by_number:
            row = bills_by_number[bill_num_normalized]

            # Get summary from summaries CSV or fall back to description
            summary = summaries_by_number.get(bill_num_normalized, '')
            if not summary:
                summary = row.get('Bill_description', 'No summary available').strip()

            # Get last action info
            house_action = row.get('Last_house_action', '').strip()
            house_action_date = row.get('Last_house_action_date', '').strip()
            senate_action = row.get('Last_senate_action', '').strip()
            senate_action_date = row.get('Last_senate_action_date', '').strip()

            # Use most recent action
            if senate_action_date and (not house_action_date or senate_action_date > house_action_date):
                last_action = senate_action
                last_action_date = senate_action_date
            else:
                last_action = house_action
                last_action_date = house_action_date

            bills_data[bill_num_normalized] = {
                'bill_number': bill_num_normalized,
                'bill_url': f"https://lis.virginia.gov/bill-details/{CURRENT_SESSION}/{bill_num_normalized}",
                'status': get_bill_status(row),
                'summary': summary,
                'last_action': last_action or 'No action recorded',
                'last_action_date': last_action_date,
                'patron': row.get('Patron_name', '').strip()
            }
            print(f"   Found {bill_num_normalized}: {bills_data[bill_num_normalized]['status']}")
        else:
            print(f"   Warning: {bill_num_normalized} not found in session {CURRENT_SESSION}")
            bills_data[bill_num_normalized] = {
                'bill_number': bill_num_normalized,
                'bill_url': f"https://lis.virginia.gov/bill-details/{CURRENT_SESSION}/{bill_num_normalized}",
                'status': 'Not Found',
                'summary': f'Bill {bill_num_normalized} not found in the {CURRENT_SESSION[:4]} session',
                'last_action': 'N/A',
                'last_action_date': ''
            }

    return bills_data

def load_previous_state() -> Dict:
    """Load the previous state of tracked bills"""
    try:
        with open(PREVIOUS_STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_current_state(data: Dict):
    """Save current state for next comparison"""
    os.makedirs(os.path.dirname(CURRENT_STATE_FILE), exist_ok=True)
    with open(CURRENT_STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def detect_changes(previous: Dict, current: Dict) -> List[Dict]:
    """Compare previous and current states to detect changes"""
    changes = []
    
    for bill_num, current_data in current.items():
        if 'error' in current_data:
            continue
            
        if bill_num not in previous:
            changes.append({
                'bill': bill_num,
                'type': 'new_tracking',
                'message': f'Started tracking {bill_num}',
                'current_status': current_data.get('status'),
                'timestamp': datetime.now().isoformat()
            })
            continue
        
        previous_data = previous[bill_num]
        
        if previous_data.get('status') != current_data.get('status'):
            changes.append({
                'bill': bill_num,
                'type': 'status_change',
                'previous_status': previous_data.get('status'),
                'current_status': current_data.get('status'),
                'message': f"{bill_num} status changed: {previous_data.get('status')} → {current_data.get('status')}",
                'timestamp': datetime.now().isoformat()
            })
        
        if previous_data.get('last_action') != current_data.get('last_action'):
            changes.append({
                'bill': bill_num,
                'type': 'action_update',
                'previous_action': previous_data.get('last_action'),
                'current_action': current_data.get('last_action'),
                'message': f"{bill_num} new action: {current_data.get('last_action')}",
                'timestamp': datetime.now().isoformat()
            })
    
    return changes

def append_to_changes_log(changes: List[Dict]):
    """Append detected changes to the running log"""
    os.makedirs(os.path.dirname(CHANGES_LOG_FILE), exist_ok=True)
    
    try:
        with open(CHANGES_LOG_FILE, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []
    
    log.extend(changes)
    log = log[-1000:]
    
    with open(CHANGES_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def generate_dashboard_html(current_data: Dict, changes: List[Dict], tracked_bills: List[str]):
    """Generate HTML dashboard with configuration interface"""
    
    now = datetime.now()
    
    # Get repository info from environment (set by GitHub Actions)
    repo_name = os.environ.get('GITHUB_REPOSITORY', 'YOUR-USERNAME/virginia-bill-tracker')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virginia Bill Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --bg-primary: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border-color: #e2e8f0;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --success: #10b981;
            --success-bg: #ecfdf5;
            --warning: #f59e0b;
            --warning-bg: #fffbeb;
            --error: #ef4444;
            --error-bg: #fef2f2;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --radius: 8px;
            --radius-lg: 12px;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            min-height: 100vh;
            padding: 24px;
            color: var(--text-primary);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: var(--bg-card);
            padding: 24px 28px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
        }}

        .header h1 {{
            color: var(--text-primary);
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}

        .header-actions {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }}

        .sync-info {{
            color: var(--text-secondary);
            font-size: 13px;
        }}

        .sync-time {{
            color: var(--accent);
            font-weight: 600;
        }}

        .btn {{
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
        }}

        .btn:hover {{
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}

        .btn:active {{
            transform: translateY(0);
        }}

        .btn-secondary {{
            background: var(--bg-primary);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }}

        .btn-secondary:hover {{
            background: var(--bg-card);
            border-color: var(--text-muted);
            color: var(--text-primary);
        }}

        .changes-banner {{
            background: var(--warning-bg);
            border: 1px solid #fcd34d;
            padding: 14px 18px;
            margin-bottom: 20px;
            border-radius: var(--radius);
            font-size: 14px;
            font-weight: 500;
            color: #92400e;
        }}

        .changes-banner.no-changes {{
            background: var(--success-bg);
            border-color: #6ee7b7;
            color: #065f46;
        }}

        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .modal.active {{
            display: flex;
            animation: fadeIn 0.15s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .modal-content {{
            background: var(--bg-card);
            padding: 28px;
            border-radius: var(--radius-lg);
            max-width: 560px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: var(--shadow-lg);
            animation: slideUp 0.2s ease;
        }}

        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }}

        .modal-header h2 {{
            color: var(--text-primary);
            font-size: 1.125rem;
            font-weight: 600;
        }}

        .close-btn {{
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: var(--text-muted);
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--radius);
            transition: all 0.15s ease;
        }}

        .close-btn:hover {{
            background: var(--bg-primary);
            color: var(--text-primary);
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 6px;
            color: var(--text-primary);
            font-weight: 500;
            font-size: 14px;
        }}

        .form-group input {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            font-size: 14px;
            font-family: inherit;
            transition: all 0.15s ease;
            background: var(--bg-card);
        }}

        .form-group input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}

        .form-help {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
            line-height: 1.5;
        }}

        .form-help a {{
            color: var(--accent);
            text-decoration: none;
        }}

        .form-help a:hover {{
            text-decoration: underline;
        }}

        .bills-list {{
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 12px;
            max-height: 180px;
            overflow-y: auto;
            background: var(--bg-primary);
        }}

        .bill-tag {{
            display: inline-flex;
            align-items: center;
            background: var(--accent);
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            margin: 3px;
            font-size: 12px;
            font-weight: 500;
        }}

        .bill-tag button {{
            background: none;
            border: none;
            color: rgba(255,255,255,0.8);
            margin-left: 6px;
            cursor: pointer;
            font-size: 14px;
            line-height: 1;
            padding: 0;
            transition: color 0.15s ease;
        }}

        .bill-tag button:hover {{
            color: white;
        }}

        .add-bill-form {{
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }}

        .add-bill-form input {{
            flex: 1;
        }}

        .alert {{
            padding: 12px 16px;
            border-radius: var(--radius);
            margin-bottom: 16px;
            font-size: 14px;
            font-weight: 500;
        }}

        .alert-info {{
            background: #eff6ff;
            color: #1e40af;
            border: 1px solid #bfdbfe;
        }}

        .alert-success {{
            background: var(--success-bg);
            color: #065f46;
            border: 1px solid #6ee7b7;
        }}

        .alert-error {{
            background: var(--error-bg);
            color: #991b1b;
            border: 1px solid #fca5a5;
        }}

        .bills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .bill-card {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
        }}

        .bill-card:hover {{
            border-color: var(--accent);
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }}

        .bill-card.has-changes {{
            border-color: var(--warning);
            background: var(--warning-bg);
        }}

        .bill-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 12px;
        }}

        .bill-number {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.025em;
        }}

        .bill-status {{
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            white-space: nowrap;
        }}

        .status-left-in-committee {{
            background: var(--warning-bg);
            color: #b45309;
        }}

        .status-in-committee,
        .status-pending {{
            background: #eff6ff;
            color: #1d4ed8;
        }}

        .status-passed,
        .status-passed-senate,
        .status-passed-house,
        .status-passed-both-chambers {{
            background: var(--success-bg);
            color: #047857;
        }}

        .status-signed-into-law {{
            background: #f0fdf4;
            color: #15803d;
        }}

        .status-failed,
        .status-vetoed {{
            background: var(--error-bg);
            color: #b91c1c;
        }}

        .status-continued {{
            background: #faf5ff;
            color: #7c3aed;
        }}

        .status-not-found {{
            background: var(--bg-primary);
            color: var(--text-muted);
        }}

        .bill-summary {{
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.65;
            margin-bottom: 16px;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
            flex-grow: 1;
        }}

        .bill-card:hover .bill-summary {{
            color: var(--text-primary);
        }}

        .bill-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
            margin-top: auto;
        }}

        .expand-hint {{
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 500;
            transition: color 0.15s ease;
        }}

        .bill-card:hover .expand-hint {{
            color: var(--accent);
        }}

        .bill-link {{
            color: var(--accent);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease;
        }}

        .bill-link:hover {{
            color: var(--accent-hover);
        }}

        .change-badge {{
            background: #fef3c7;
            color: #b45309;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-left: 8px;
        }}

        .changes-section {{
            background: var(--bg-card);
            padding: 24px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
        }}

        .changes-section h2 {{
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 16px;
        }}

        .change-item {{
            padding: 12px 14px;
            background: var(--bg-primary);
            border-radius: var(--radius);
            margin-bottom: 8px;
            border-left: 3px solid var(--accent);
        }}

        .change-item:last-child {{
            margin-bottom: 0;
        }}

        .change-timestamp {{
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 4px;
        }}

        .no-bills {{
            background: var(--bg-card);
            padding: 48px;
            border-radius: var(--radius-lg);
            text-align: center;
            border: 1px solid var(--border-color);
        }}

        .no-bills h2 {{
            color: var(--text-primary);
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .no-bills p {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        .loading {{
            text-align: center;
            padding: 24px;
            color: var(--text-muted);
        }}

        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: transparent;
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Virginia Bill Tracker</h1>
            <div class="header-actions">
                <div class="sync-info">
                    Last synced: <span class="sync-time">{now.strftime('%B %d, %Y at %I:%M %p ET')}</span>
                </div>
                <button class="btn" onclick="openConfigModal()">⚙️ Configure Bills</button>
            </div>
        </div>
        
"""
    # Filter out 'new_tracking' for the banner - only show actual status/action changes
    actual_changes = [c for c in changes if c.get('type') != 'new_tracking']

    html += f"""
        <div class="changes-banner {'no-changes' if not actual_changes else ''}">
            <strong>{'✅ No changes detected' if not actual_changes else f'⚠️ {len(actual_changes)} change(s) detected since last sync'}</strong>
        </div>
"""

    # Initialize bills data for detail modal
    bills_json_data = {}

    if not current_data:
        html += """
        <div class="no-bills">
            <h2>No Bills Tracked</h2>
            <p>Click "Configure Bills" above to add bills to track</p>
        </div>
"""
    else:
        # Only mark bills as "UPDATED" for actual changes, not newly tracked bills
        changed_bills = {change['bill'] for change in changes if change.get('type') != 'new_tracking'}
        
        html += '        <div class="bills-grid">\n'

        for bill_num, data in sorted(current_data.items()):
            if 'error' in data:
                continue

            has_changes = bill_num in changed_bills
            status_class = data.get('status', '').lower().replace(' ', '-')

            # Store data for modal
            bills_json_data[bill_num] = {
                'bill_number': bill_num,
                'status': data.get('status', 'Unknown'),
                'summary': data.get('summary', 'No summary available'),
                'last_action': data.get('last_action', ''),
                'last_action_date': data.get('last_action_date', ''),
                'patron': data.get('patron', ''),
                'bill_url': data.get('bill_url', '#')
            }

            html += f"""
            <div class="bill-card {'has-changes' if has_changes else ''}" onclick="openBillDetail('{bill_num}')">
                <div class="bill-header">
                    <div class="bill-number">
                        {bill_num}
                        {f'<span class="change-badge">UPDATED</span>' if has_changes else ''}
                    </div>
                    <div class="bill-status status-{status_class}">
                        {data.get('status', 'Unknown')}
                    </div>
                </div>
                <div class="bill-summary">
                    {data.get('summary', 'No summary available')}
                </div>
                <div class="bill-footer">
                    <span class="expand-hint">Click to view details</span>
                    <a href="{data.get('bill_url', '#')}" target="_blank" class="bill-link" onclick="event.stopPropagation()">
                        View on LIS →
                    </a>
                </div>
            </div>
"""
        
        html += '        </div>\n'
        
        if changes:
            html += """
        <div class="changes-section">
            <h2>Recent Changes</h2>
"""
            for change in changes[-10:]:
                html += f"""
            <div class="change-item">
                <div>{change.get('message', '')}</div>
                <div class="change-timestamp">
                    {datetime.fromisoformat(change['timestamp']).strftime('%B %d, %Y at %I:%M %p')}
                </div>
            </div>
"""
            html += """
        </div>
"""
    
    # Configuration Modal and Bill Detail Modal
    tracked_bills_json = json.dumps(tracked_bills)
    # Encode bills data for JavaScript
    bills_data_json = json.dumps(bills_json_data)

    html += f"""
    <!-- Bill Detail Modal -->
    <div id="billDetailModal" class="modal">
        <div class="modal-content detail-modal">
            <div class="modal-header">
                <h2 id="detailBillNumber">Bill Details</h2>
                <button class="close-btn" onclick="closeBillDetail()">&times;</button>
            </div>

            <div class="detail-meta">
                <span class="detail-status-pill" id="detailBillStatus"></span>
                <span class="detail-patron" id="detailPatron"></span>
            </div>

            <div class="detail-section">
                <div class="detail-label">Summary</div>
                <p id="detailSummary" class="detail-summary-full"></p>
            </div>

            <div class="detail-section" id="detailActionSection">
                <div class="detail-label">Last Action</div>
                <div class="detail-action-box">
                    <p id="detailLastAction" class="detail-action-text"></p>
                    <p class="detail-date" id="detailLastActionDate"></p>
                </div>
            </div>

            <div class="detail-footer">
                <button class="btn btn-secondary" onclick="closeBillDetail()">Close</button>
                <a id="detailLisLink" href="#" target="_blank" class="btn">View on LIS →</a>
            </div>
        </div>
    </div>

    <style>
        .detail-modal {{
            max-width: 650px;
        }}
        .detail-meta {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e7eb;
        }}
        .detail-status-pill {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .detail-status-pill.status-left-in-committee {{
            background: #fef3c7;
            color: #92400e;
        }}
        .detail-status-pill.status-passed-senate,
        .detail-status-pill.status-passed-house,
        .detail-status-pill.status-passed-both-chambers {{
            background: #d1fae5;
            color: #065f46;
        }}
        .detail-status-pill.status-signed-into-law {{
            background: #c7d2fe;
            color: #3730a3;
        }}
        .detail-status-pill.status-vetoed,
        .detail-status-pill.status-failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .detail-status-pill.status-in-committee,
        .detail-status-pill.status-pending {{
            background: #dbeafe;
            color: #1e40af;
        }}
        .detail-patron {{
            color: #6b7280;
            font-size: 14px;
            font-style: italic;
        }}
        .detail-section {{
            margin-bottom: 24px;
        }}
        .detail-label {{
            color: #6b7280;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .detail-summary-full {{
            color: #1f2937;
            font-size: 15px;
            line-height: 1.75;
            margin: 0;
        }}
        .detail-action-box {{
            background: #f9fafb;
            border-radius: 8px;
            padding: 12px 16px;
            border-left: 3px solid #667eea;
        }}
        .detail-action-text {{
            color: #374151;
            font-size: 14px;
            line-height: 1.5;
            margin: 0;
        }}
        .detail-date {{
            color: #9ca3af;
            font-size: 12px;
            margin-top: 6px;
        }}
        .detail-footer {{
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
        }}
    </style>

    <!-- Configuration Modal -->
    <div id="configModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Configure Tracked Bills</h2>
                <button class="close-btn" onclick="closeConfigModal()">&times;</button>
            </div>
            
            <div id="alertContainer"></div>
            
            <div class="form-group">
                <label>GitHub Personal Access Token</label>
                <input type="password" id="githubToken" placeholder="ghp_xxxxxxxxxxxx" onchange="saveTokenToStorage()">
                <div class="form-help">
                    Required to save changes. Your token is saved locally in your browser for convenience.
                    <br>Create one at:
                    <a href="https://github.com/settings/tokens/new?scopes=repo&description=Virginia%20Bill%20Tracker" target="_blank">
                        GitHub Settings → Tokens
                    </a>
                    (select "repo" scope)
                </div>
            </div>
            
            <div class="form-group">
                <label>Tracked Bills</label>
                <div class="bills-list" id="billsList">
                    <!-- Bills will be rendered here -->
                </div>
                <div class="add-bill-form">
                    <input type="text" id="newBillInput" placeholder="Enter bill ID (e.g., HB1, SB200)" 
                           onkeypress="if(event.key==='Enter')addBill()">
                    <button class="btn" onclick="addBill()">Add Bill</button>
                </div>
                <div class="form-help">
                    Find bill IDs at: <a href="https://lis.virginia.gov/bill-search" target="_blank">Virginia LIS</a>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeConfigModal()">Cancel</button>
                <button class="btn" onclick="saveConfiguration()">💾 Save Changes</button>
            </div>
        </div>
    </div>
    
    <script>
        // Configuration data
        let trackedBills = {tracked_bills_json};
        const REPO_NAME = '{repo_name}';
        const CONFIG_FILE_PATH = 'bills_to_track.json';

        // Bills data for detail modal
        const billsData = {bills_data_json};

        // Bill Detail Modal functions
        function openBillDetail(billNum) {{
            const bill = billsData[billNum];
            if (!bill) return;

            document.getElementById('detailBillNumber').textContent = bill.bill_number;
            const statusEl = document.getElementById('detailBillStatus');
            statusEl.textContent = bill.status;
            statusEl.className = 'detail-status-pill status-' + bill.status.toLowerCase().replace(/ /g, '-');
            document.getElementById('detailSummary').textContent = bill.summary;
            document.getElementById('detailLisLink').href = bill.bill_url;

            // Show patron if available
            const patronEl = document.getElementById('detailPatron');
            if (bill.patron) {{
                patronEl.textContent = 'Patron: ' + bill.patron;
                patronEl.style.display = 'inline';
            }} else {{
                patronEl.style.display = 'none';
            }}

            // Show last action if available
            const actionSection = document.getElementById('detailActionSection');
            if (bill.last_action && bill.last_action !== 'No action recorded') {{
                document.getElementById('detailLastAction').textContent = bill.last_action;
                document.getElementById('detailLastActionDate').textContent = bill.last_action_date || '';
                actionSection.style.display = 'block';
            }} else {{
                actionSection.style.display = 'none';
            }}

            document.getElementById('billDetailModal').classList.add('active');
        }}

        function closeBillDetail() {{
            document.getElementById('billDetailModal').classList.remove('active');
        }}

        // Close detail modal on outside click
        document.getElementById('billDetailModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeBillDetail();
            }}
        }});

        // Render bills list
        function renderBillsList() {{
            const container = document.getElementById('billsList');
            if (trackedBills.length === 0) {{
                container.innerHTML = '<p style="color: #666; padding: 10px;">No bills tracked yet. Add one below.</p>';
                return;
            }}
            
            container.innerHTML = trackedBills.map(bill => 
                `<span class="bill-tag">
                    ${{bill}}
                    <button onclick="removeBill('${{bill}}')">&times;</button>
                </span>`
            ).join('');
        }}
        
        // Add bill
        function addBill() {{
            const input = document.getElementById('newBillInput');
            let billId = input.value.trim().toUpperCase();
            
            if (!billId) return;
            
            // Validate format (HB/SB followed by number)
            if (!billId.match(/^(HB|SB|HJR|SJR|HR|SR)\\d+$/i)) {{
                showAlert('Please enter a valid bill ID (e.g., HB1, SB200)', 'error');
                return;
            }}
            
            if (trackedBills.includes(billId)) {{
                showAlert('Bill already tracked', 'error');
                return;
            }}
            
            trackedBills.push(billId);
            trackedBills.sort();
            input.value = '';
            renderBillsList();
            showAlert('Bill added. Click "Save Changes" to update.', 'info');
        }}
        
        // Remove bill
        function removeBill(billId) {{
            trackedBills = trackedBills.filter(b => b !== billId);
            renderBillsList();
            showAlert('Bill removed. Click "Save Changes" to update.', 'info');
        }}
        
        // Save configuration to GitHub
        async function saveConfiguration() {{
            const token = document.getElementById('githubToken').value.trim();
            
            if (!token) {{
                showAlert('Please enter your GitHub Personal Access Token', 'error');
                return;
            }}
            
            if (trackedBills.length === 0) {{
                showAlert('Please add at least one bill before saving', 'error');
                return;
            }}
            
            showAlert('Saving...', 'info');
            
            try {{
                // Prepare new content
                const newConfig = {{
                    bills: trackedBills,
                    settings: {{
                        notification_email: null,
                        sync_frequency: "daily",
                        timezone: "America/New_York"
                    }}
                }};
                
                const content = btoa(JSON.stringify(newConfig, null, 2));
                
                // Try to get current file to check if it exists
                const getResponse = await fetch(`https://api.github.com/repos/${{REPO_NAME}}/contents/${{CONFIG_FILE_PATH}}`, {{
                    headers: {{
                        'Authorization': `token ${{token}}`,
                        'Accept': 'application/vnd.github.v3+json'
                    }}
                }});
                
                let sha = null;
                let method = 'PUT';
                let commitMessage = '';
                
                if (getResponse.ok) {{
                    // File exists - update it
                    const currentFile = await getResponse.json();
                    sha = currentFile.sha;
                    commitMessage = `Update tracked bills via web interface - ${{new Date().toISOString()}}`;
                }} else if (getResponse.status === 404) {{
                    // File doesn't exist - create it
                    commitMessage = `Create bills_to_track.json via web interface - ${{new Date().toISOString()}}`;
                }} else {{
                    // Some other error
                    const errorData = await getResponse.json();
                    throw new Error(errorData.message || 'Failed to check configuration file. Verify your token has repo access.');
                }}
                
                // Create or update file
                const saveBody = {{
                    message: commitMessage,
                    content: content
                }};
                
                // Only include sha if file exists (for update)
                if (sha) {{
                    saveBody.sha = sha;
                }}
                
                const saveResponse = await fetch(`https://api.github.com/repos/${{REPO_NAME}}/contents/${{CONFIG_FILE_PATH}}`, {{
                    method: 'PUT',
                    headers: {{
                        'Authorization': `token ${{token}}`,
                        'Accept': 'application/vnd.github.v3+json',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(saveBody)
                }});
                
                if (!saveResponse.ok) {{
                    const error = await saveResponse.json();
                    
                    // Provide helpful error messages
                    let errorMessage = error.message || 'Failed to save configuration';
                    
                    if (error.message && error.message.includes('Bad credentials')) {{
                        errorMessage = 'Invalid token. Please check your GitHub Personal Access Token.';
                    }} else if (error.message && error.message.includes('Not Found')) {{
                        errorMessage = 'Repository not found. Check that the repository name is correct.';
                    }} else if (error.message && error.message.includes('Resource not accessible')) {{
                        errorMessage = 'Token does not have access. Make sure your token has "repo" scope.';
                    }}
                    
                    throw new Error(errorMessage);
                }}
                
                showAlert('✅ Configuration saved! Changes will take effect on next sync.', 'success');
                
                // Save token to localStorage for future use
                saveTokenToStorage();

            }} catch (error) {{
                showAlert(`Error: ${{error.message}}`, 'error');
                console.error('Save error:', error);
            }}
        }}
        
        // Show alert
        function showAlert(message, type) {{
            const container = document.getElementById('alertContainer');
            const alertClass = type === 'error' ? 'alert-error' : 
                              type === 'success' ? 'alert-success' : 'alert-info';
            
            container.innerHTML = `<div class="alert ${{alertClass}}">${{message}}</div>`;
            
            if (type === 'success') {{
                setTimeout(() => {{
                    container.innerHTML = '';
                    closeConfigModal();
                    location.reload();
                }}, 3000);
            }}
        }}
        
        // Token storage key
        const TOKEN_STORAGE_KEY = 'va_bill_tracker_github_token';

        // Modal controls
        function openConfigModal() {{
            document.getElementById('configModal').classList.add('active');
            renderBillsList();
            // Load saved token from localStorage
            const savedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
            if (savedToken) {{
                document.getElementById('githubToken').value = savedToken;
            }}
        }}

        function closeConfigModal() {{
            document.getElementById('configModal').classList.remove('active');
            document.getElementById('alertContainer').innerHTML = '';
        }}

        // Save token to localStorage when user types
        function saveTokenToStorage() {{
            const token = document.getElementById('githubToken').value.trim();
            if (token) {{
                localStorage.setItem(TOKEN_STORAGE_KEY, token);
            }}
        }}
        
        // Close modal on outside click
        document.getElementById('configModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeConfigModal();
            }}
        }});
        
        // Initialize
        renderBillsList();
    </script>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Main execution function"""
    print("🏛️  Virginia Bill Tracker Starting...")
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    bills_to_track = load_bills_to_track()
    print(f"📋 Tracking {len(bills_to_track)} bills: {', '.join(bills_to_track)}")
    
    if not bills_to_track:
        print("⚠️  No bills configured for tracking!")
    
    print("🔄 Fetching current bill data...")
    current_data = fetch_bill_data(bills_to_track)
    
    previous_data = load_previous_state()
    
    print("🔍 Detecting changes...")
    changes = detect_changes(previous_data, current_data)
    
    if changes:
        print(f"⚠️  Detected {len(changes)} change(s):")
        for change in changes:
            print(f"   - {change['message']}")
    else:
        print("✅ No changes detected")
    
    save_current_state(current_data)
    
    if changes:
        append_to_changes_log(changes)
    
    print("📊 Generating dashboard...")
    dashboard_html = generate_dashboard_html(current_data, changes, bills_to_track)
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w') as f:
        f.write(dashboard_html)
    
    print("✅ Dashboard generated at docs/index.html")
    print("🎉 Done!")

if __name__ == "__main__":
    main()
