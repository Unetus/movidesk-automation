#!/usr/bin/env python3
"""Direct API check without cache."""

import httpx
import json
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
API_TOKEN = os.getenv('MOVIDESK_TOKEN')
BASE_URL = 'https://api.movidesk.com/public/v1'

print("\n" + "="*60)
print("CHECK DIRETO NA API (sem cache)")
print("="*60 + "\n")

# Add timestamp to force fresh data
import time
timestamp = int(time.time())

response = httpx.get(
    f'{BASE_URL}/tickets',
    params={
        '$select': 'id,protocol,subject,slaSolutionDate,lastUpdate,createdDate,baseStatus',
        '$filter': 'id eq 60271',
        'token': API_TOKEN,
        '_': timestamp  # Cache buster
    },
    timeout=10.0
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        ticket = data[0]
        print("\n📋 Dados do Ticket #60271:")
        print(json.dumps(ticket, indent=2, ensure_ascii=False))
        
        sla = ticket.get('slaSolutionDate')
        if sla:
            print(f"\n⏰ Análise:")
            print(f"   slaSolutionDate: {sla}")
            print(f"   Hora atual: {datetime.now()}")
            
            # Parse SLA date
            from datetime import datetime
            sla_dt = datetime.fromisoformat(sla.replace('Z', '+00:00'))
            if sla_dt.tzinfo:
                sla_dt = sla_dt.replace(tzinfo=None)
            
            now = datetime.now()
            diff = (now - sla_dt).total_seconds()
            
            if diff > 0:
                print(f"   🔴 VENCIDO há {diff / 3600:.1f} horas ({diff / 60:.0f} min)")
            else:
                print(f"   ✅ Faltam {abs(diff) / 3600:.1f} horas")
    else:
        print(f"Resultado: {data}")
else:
    print(f"Erro: {response.text}")

print("\n" + "="*60)
