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
# Virginia LIS data URL - 20251 = 2025 Regular Session
LIS_DATA_BASE_URL = "https://lis.blob.core.windows.net/lisfiles"
CURRENT_SESSION = "20251"
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
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .header-actions {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
        }}
        .sync-info {{
            color: #666;
            font-size: 14px;
        }}
        .sync-time {{
            color: #667eea;
            font-weight: 600;
        }}
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.2s;
        }}
        .btn:hover {{
            background: #5568d3;
        }}
        .btn-secondary {{
            background: #6b7280;
        }}
        .btn-secondary:hover {{
            background: #4b5563;
        }}
        .changes-banner {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .changes-banner.no-changes {{
            background: #d1fae5;
            border-left-color: #10b981;
        }}
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        .modal.active {{
            display: flex;
        }}
        .modal-content {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .modal-header h2 {{
            color: #333;
        }}
        .close-btn {{
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-group label {{
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 600;
        }}
        .form-group input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        .form-help {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .bills-list {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
            background: #f9fafb;
        }}
        .bill-tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            margin: 3px;
            font-size: 12px;
        }}
        .bill-tag button {{
            background: none;
            border: none;
            color: white;
            margin-left: 5px;
            cursor: pointer;
            font-weight: bold;
        }}
        .add-bill-form {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .add-bill-form input {{
            flex: 1;
        }}
        .alert {{
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        .alert-info {{
            background: #dbeafe;
            color: #1e40af;
            border-left: 4px solid #3b82f6;
        }}
        .alert-success {{
            background: #d1fae5;
            color: #065f46;
            border-left: 4px solid #10b981;
        }}
        .alert-error {{
            background: #fee2e2;
            color: #991b1b;
            border-left: 4px solid #ef4444;
        }}
        
        .bills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .bill-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .bill-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .bill-card.has-changes {{
            border: 2px solid #f59e0b;
            background: #fffbeb;
        }}
        .bill-number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .bill-status {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .status-in-committee {{
            background: #dbeafe;
            color: #1e40af;
        }}
        .status-passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status-failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .bill-summary {{
            color: #666;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .bill-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }}
        .bill-link:hover {{
            text-decoration: underline;
        }}
        .change-badge {{
            background: #fef3c7;
            color: #92400e;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }}
        .changes-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .changes-section h2 {{
            color: #333;
            margin-bottom: 15px;
        }}
        .change-item {{
            padding: 12px;
            border-left: 3px solid #f59e0b;
            background: #fffbeb;
            margin-bottom: 10px;
            border-radius: 4px;
        }}
        .change-timestamp {{
            color: #666;
            font-size: 12px;
        }}
        .no-bills {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            color: #666;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            color: #666;
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
        
        <div class="changes-banner {'no-changes' if not changes else ''}">
            <strong>{'✅ No changes detected' if not changes else f'⚠️ {len(changes)} change(s) detected since last sync'}</strong>
        </div>
"""
    
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
            
            html += f"""
            <div class="bill-card {'has-changes' if has_changes else ''}">
                <div class="bill-number">
                    {bill_num}
                    {f'<span class="change-badge">UPDATED</span>' if has_changes else ''}
                </div>
                <div class="bill-status status-{status_class}">
                    {data.get('status', 'Unknown')}
                </div>
                <div class="bill-summary">
                    {data.get('summary', 'No summary available')}
                </div>
                <a href="{data.get('bill_url', '#')}" target="_blank" class="bill-link">
                    View on LIS →
                </a>
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
    
    # Configuration Modal
    tracked_bills_json = json.dumps(tracked_bills)
    
    html += f"""
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
                <input type="password" id="githubToken" placeholder="ghp_xxxxxxxxxxxx">
                <div class="form-help">
                    Required to save changes. Create one at: 
                    <a href="https://github.com/settings/tokens/new?scopes=repo&description=Virginia%20Bill%20Tracker" target="_blank">
                        GitHub Settings → Tokens
                    </a>
                    <br>Select "repo" scope when creating the token.
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
                
                // Clear token for security
                setTimeout(() => {{
                    document.getElementById('githubToken').value = '';
                }}, 2000);
                
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
        
        // Modal controls
        function openConfigModal() {{
            document.getElementById('configModal').classList.add('active');
            renderBillsList();
        }}
        
        function closeConfigModal() {{
            document.getElementById('configModal').classList.remove('active');
            document.getElementById('alertContainer').innerHTML = '';
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
