"""Debug script to check fields returned by Movidesk API - minimal approach."""

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

# Build API request - usar APENAS campos que SABEMOS que funcionam
url = f"{MOVIDESK_BASE_URL}/tickets"
params = {
    'token': MOVIDESK_TOKEN,
    # Apenas campos confirmados como válidos
    '$select': 'id,protocol,subject,category,urgency,status,baseStatus,owner,clients,createdDate,lastUpdate,actions,serviceFull',
    '$filter': f"owner/email eq '{AGENT_EMAIL}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
    '$top': 1,
    '$orderby': 'lastUpdate desc'
}

print(f"Fetching first ticket for: {AGENT_EMAIL}\n")

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        tickets = response.json()
        
        if tickets and isinstance(tickets, list) and len(tickets) > 0:
            ticket = tickets[0]
            
            print("="*80)
            print(f"RAW API RESPONSE - TICKET #{ticket.get('protocol', ticket.get('id', 'unknown'))}")
            print("="*80)
            print(json.dumps(ticket, indent=2, ensure_ascii=False, default=str))
            print("="*80)
            
            # List all fields
            print("\n>>> ALL FIELDS IN RESPONSE <<<\n")
            def print_fields(d, prefix=""):
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        print(f"  {full_key}: [object]")
                        print_fields(value, full_key)
                    elif isinstance(value, list):
                        if len(value) > 0 and isinstance(value[0], dict):
                            print(f"  {full_key}: [array of {len(value)} objects]")
                            print_fields(value[0], f"{full_key}[0]")
                        else:
                            print(f"  {full_key}: {value}")
                    else:
                        print(f"  {full_key}: {value}")
            
            print_fields(ticket)
            
        else:
            print("❌ No tickets found")
            
except Exception as e:
    print(f"ERROR: {e}")
