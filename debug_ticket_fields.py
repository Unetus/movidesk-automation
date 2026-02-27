"""Debug script to check all fields returned by Movidesk API."""

import httpx
import json
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

MOVIDESK_TOKEN = os.getenv('MOVIDESK_TOKEN')
MOVIDESK_BASE_URL = os.getenv('MOVIDESK_BASE_URL', 'https://api.movidesk.com/public/v1')
AGENT_EMAIL = os.getenv('MOVIDESK_AGENT_EMAIL')

if not all([MOVIDESK_TOKEN, AGENT_EMAIL]):
    print("ERROR: Missing required environment variables")
    exit(1)

# Build API request
url = f"{MOVIDESK_BASE_URL}/tickets"
params = {
    'token': MOVIDESK_TOKEN,
    '$select': 'id,protocol,subject,baseStatus,status,urgency,createdDate,lastUpdate,serviceFull',
    '$filter': f"owner/email eq '{AGENT_EMAIL}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
    '$top': 3,
    '$orderby': 'lastUpdate desc'
}

print(f"Fetching tickets for: {AGENT_EMAIL}")
print(f"URL: {url}")
print(f"Params: {json.dumps(params, indent=2)}\n")

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        
        tickets = response.json()
        
        if isinstance(tickets, list):
            print(f"Found {len(tickets)} open tickets\n")
            print("="*80)
            
            for i, ticket in enumerate(tickets):
                print(f"\n### TICKET #{i+1} ###")
                print(json.dumps(ticket, indent=2, ensure_ascii=False))
                
                # Highlight serviceFull
                if 'serviceFull' in ticket:
                    print("\n<<<< serviceFull DETAILS >>>>")
                    if ticket['serviceFull']:
                        for j, service in enumerate(ticket['serviceFull']):
                            print(f"\nService [{j}]:")
                            print(json.dumps(service, indent=2, ensure_ascii=False))
                            if 'resolutionDate' in service:
                                print(f"✅ resolutionDate FOUND: {service['resolutionDate']}")
                
                print("="*80)
        else:
            print("Single ticket response:")
            print(json.dumps(tickets, indent=2, ensure_ascii=False))
            
except Exception as e:
    print(f"ERROR: {e}")
    if hasattr(e, 'response'):
        print(f"Response: {e.response.text}")
