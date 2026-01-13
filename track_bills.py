#!/usr/bin/env python3
"""
Virginia Legislative Bill Tracker
Fetches bill status and highlights changes
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Set
import os

# Configuration
BILLS_TO_TRACK_FILE = "bills_to_track.json"
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

def fetch_bill_data(bill_numbers: List[str]) -> Dict:
    """
    Fetch current data for specified bills from Virginia LIS
    Uses the same data source we found: window.allBillsData
    """
    # Base URL for Virginia LIS API
    base_url = "https://lis.virginia.gov"
    
    # In production, you would fetch from the actual API
    # For now, we'll create a function that can be adapted
    
    bills_data = {}
    
    for bill_num in bill_numbers:
        try:
            # Construct the bill details URL
            bill_url = f"{base_url}/cgi-bin/legp604.exe?ses=261&typ=bil&val={bill_num}"
            
            # Make request (you may need to add headers/session handling)
            # This is a placeholder - actual implementation would parse the page
            
            # For now, return structure that matches what we need
            bills_data[bill_num] = {
                'bill_number': bill_num,
                'bill_url': f"https://lis.virginia.gov/bill-details/20261/{bill_num}",
                'status': 'Unknown',  # Will be scraped from page
                'summary': '',  # Will be scraped from page
                'last_action': '',  # Will be scraped from page
                'last_action_date': ''  # Will be scraped from page
            }
            
        except Exception as e:
            print(f"Error fetching {bill_num}: {str(e)}")
            bills_data[bill_num] = {'error': str(e)}
    
    return bills_data

def fetch_bills_from_search_page() -> Dict:
    """
    Alternative method: Fetch from the search page that has all bills
    This mimics what we did earlier with window.allBillsData
    """
    search_url = "https://lis.virginia.gov/bill-search"
    
    # You would need to:
    # 1. Load the page with requests or selenium
    # 2. Execute JavaScript to get window.allBillsData
    # 3. Filter for only the bills you're tracking
    
    # For a working implementation, you might use:
    # - requests + beautifulsoup for HTML parsing
    # - selenium for JavaScript execution
    # - playwright for modern browser automation
    
    return {}

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
            
        # New bill being tracked
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
        
        # Status changed
        if previous_data.get('status') != current_data.get('status'):
            changes.append({
                'bill': bill_num,
                'type': 'status_change',
                'previous_status': previous_data.get('status'),
                'current_status': current_data.get('status'),
                'message': f"{bill_num} status changed: {previous_data.get('status')} → {current_data.get('status')}",
                'timestamp': datetime.now().isoformat()
            })
        
        # Last action changed
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
    
    # Load existing log
    try:
        with open(CHANGES_LOG_FILE, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []
    
    # Append new changes
    log.extend(changes)
    
    # Keep only last 1000 changes to prevent file from growing too large
    log = log[-1000:]
    
    # Save updated log
    with open(CHANGES_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def generate_dashboard_html(current_data: Dict, changes: List[Dict]):
    """Generate HTML dashboard showing current status and recent changes"""
    
    now = datetime.now()
    
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
        .sync-info {{
            color: #666;
            font-size: 14px;
        }}
        .sync-time {{
            color: #667eea;
            font-weight: 600;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Virginia Bill Tracker</h1>
            <div class="sync-info">
                Last synced: <span class="sync-time">{now.strftime('%B %d, %Y at %I:%M %p ET')}</span>
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
            <p>Add bill IDs to bills_to_track.json to start monitoring</p>
        </div>
"""
    else:
        # Bills that changed
        changed_bills = {change['bill'] for change in changes}
        
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
        
        # Recent changes section
        if changes:
            html += """
        <div class="changes-section">
            <h2>Recent Changes</h2>
"""
            for change in changes[-10:]:  # Show last 10 changes
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
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Main execution function"""
    print("🏛️  Virginia Bill Tracker Starting...")
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    bills_to_track = load_bills_to_track()
    print(f"📋 Tracking {len(bills_to_track)} bills: {', '.join(bills_to_track)}")
    
    if not bills_to_track:
        print("⚠️  No bills configured for tracking!")
        return
    
    # Fetch current data
    print("🔄 Fetching current bill data...")
    current_data = fetch_bill_data(bills_to_track)
    
    # Load previous state
    previous_data = load_previous_state()
    
    # Detect changes
    print("🔍 Detecting changes...")
    changes = detect_changes(previous_data, current_data)
    
    if changes:
        print(f"⚠️  Detected {len(changes)} change(s):")
        for change in changes:
            print(f"   - {change['message']}")
    else:
        print("✅ No changes detected")
    
    # Save current state as previous state for next run
    save_current_state(current_data)
    
    # Append to changes log
    if changes:
        append_to_changes_log(changes)
    
    # Generate dashboard
    print("📊 Generating dashboard...")
    dashboard_html = generate_dashboard_html(current_data, changes)
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w') as f:
        f.write(dashboard_html)
    
    print("✅ Dashboard generated at docs/index.html")
    print("🎉 Done!")

if __name__ == "__main__":
    main()
