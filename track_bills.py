#!/usr/bin/env python3
"""
Virginia Legislative Bill Tracker
Fetches bill status and highlights changes
Now includes web-based configuration interface
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
    """
    bills_data = {}
    
    for bill_num in bill_numbers:
        try:
            # Placeholder - actual implementation would scrape from Virginia LIS
            bills_data[bill_num] = {
                'bill_number': bill_num,
                'bill_url': f"https://lis.virginia.gov/bill-details/20261/{bill_num}",
                'status': 'In Committee',
                'summary': f'Summary for {bill_num}',
                'last_action': 'Referred to committee',
                'last_action_date': datetime.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            print(f"Error fetching {bill_num}: {str(e)}")
            bills_data[bill_num] = {'error': str(e)}
    
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
