#!/usr/bin/env python3
"""Quick script to test overdue detection."""

import sys
sys.path.append('.')

from datetime import datetime
from src.config import get_settings
from src.api.client import MovideskClient
from src.utils.logger import get_logger

logger = get_logger()
settings = get_settings()

# Initialize client
client = MovideskClient()

# Get tickets (límite menor para testar mais rápido)
print("\n" + "="*60)
print("TESTE: Verificando tickets com SLA")
print("="*60 + "\n")

# Apenas buscar alguns tickets abertos
tickets = client.get_tickets(
    filter_expr=f"owner/email eq '{settings.movidesk_agent_email}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
    top=10,  # Apenas 10 tickets para teste rápido
    order_by='lastUpdate desc'
)

print(f"Total de tickets abertos: {len(tickets)}\n")

# Analyze each ticket
tickets_with_sla = 0
overdue_count = 0

for ticket in tickets:
    has_sla = ticket.slaSolutionDate is not None
    is_overdue = ticket.is_overdue
    
    if has_sla:
        tickets_with_sla += 1
        if is_overdue:
            overdue_count += 1
    
    print(f"Ticket #{ticket.ticket_number}: {ticket.subject[:40]}...")
    print(f"   SLA Date: {ticket.slaSolutionDate}")
    print(f"   É vencido? {is_overdue}")
    if is_overdue:
        print(f"   🔴 VENCIDO HÁ {ticket.days_overdue} dias!")
    print()

print("=" * 60)
print(f"📊 Resumo:")
print(f"   Total de tickets: {len(tickets)}")
print(f"   Com SLA definido: {tickets_with_sla}")
print(f"   Vencidos: {overdue_count}")
print(f"   Hora atual: {datetime.now()}")
print("=" * 60)

