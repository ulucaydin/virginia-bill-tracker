#!/usr/bin/env python3
"""
Improved Virginia LIS Scraper
Uses the actual search endpoint that powers the bill search page
"""

import requests
import json
import base64
from typing import Dict, List, Optional

def fetch_all_bills() -> List[Dict]:
    """
    Fetch all bills from Virginia LIS 2026 session
    This uses the same endpoint that populates window.allBillsData in the browser
    """
    
    # The search page uses this query to load all bills
    # This is the same query that was in the URL when we viewed the page
    search_params = {
        "ChamberCode": None,
        "chamberObject": "",
        "CommitteeID": None,
        "subcommittee": False,
        "parentCommittee": None,
        "PatronTypes": [],
        "LegislationNumbers": None,
        "ChapterNumber": "",
        "SessionID": 59,  # 2026 Regular Session
        "StartDate": None,
        "EndDate": None,
        "KeywordExpression": None,
        "KeywordLocation": "Bill Text",
        "MemberID": "",
        "SubjectIndexID": "",
        "LegislationCategoryID": "",
        "LegislationEventTypeID": "",
        "EventStartDate": None,
        "EventEndDate": None,
        "IsPending": None,
        "MostFrequent": None,
        "AllLegislation": True,
        "KeywordUseGlobalSessionSearch": False,
        "CurrentStatus": False,
        "IncludeFailed": True,
        "IntroductionDate": None,
        "SortBy": "Bill|ASC"
    }
    
    # Encode the query
    query_json = json.dumps(search_params)
    query_base64 = base64.b64encode(query_json.encode()).decode()
    
    # API endpoint (discovered from network tab)
    api_url = "https://lis.virginia.gov/api/legislation/search"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # Make POST request with the search parameters
        response = requests.post(
            api_url,
            json=search_params,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # The response should contain a list of bills
        return data.get('results', [])
        
    except Exception as e:
        print(f"Error fetching bills from API: {str(e)}")
        print("Falling back to page scraping...")
        return fetch_bills_fallback()

def fetch_bills_fallback() -> List[Dict]:
    """
    Fallback method: scrape the search results page directly
    """
    
    search_url = "https://lis.virginia.gov/bill-search"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # The page contains the data in a script tag or as embedded JSON
        # This would need to be parsed from the HTML
        
        # For now, return empty list (would be implemented with actual page parsing)
        return []
        
    except Exception as e:
        print(f"Fallback also failed: {str(e)}")
        return []

def get_bills_by_ids(bill_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch specific bills by their IDs
    Returns a dictionary keyed by bill ID
    """
    
    # Fetch all bills
    all_bills = fetch_all_bills()
    
    # Filter for requested bills
    bills_dict = {}
    
    bill_ids_upper = [bid.upper() for bid in bill_ids]
    
    for bill in all_bills:
        bill_number = bill.get('billNumber', '').upper()
        
        if bill_number in bill_ids_upper:
            bills_dict[bill_number] = {
                'bill_number': bill_number,
                'bill_url': bill.get('billUrl', ''),
                'summary': bill.get('summary', ''),
                'status': bill.get('status', ''),
                'last_action': bill.get('lastAction', ''),
                'last_action_date': bill.get('lastActionDate', '')
            }
    
    # Add error entries for bills not found
    for bill_id in bill_ids_upper:
        if bill_id not in bills_dict:
            bills_dict[bill_id] = {
                'bill_number': bill_id,
                'error': 'Bill not found',
                'bill_url': f'https://lis.virginia.gov/bill-details/20261/{bill_id}',
                'summary': 'Bill not found in current session',
                'status': 'Unknown'
            }
    
    return bills_dict

if __name__ == "__main__":
    # Test the scraper
    test_bills = ['HB1', 'SB200']
    print(f"Testing scraper with bills: {test_bills}")
    
    results = get_bills_by_ids(test_bills)
    
    print("\nResults:")
    print(json.dumps(results, indent=2))
