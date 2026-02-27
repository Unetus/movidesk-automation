#!/usr/bin/env python3
"""Find tickets with SLA in the past (truly overdue)."""

import sys
sys.path.append('.')

from datetime import datetime
from src.config import get_settings
from src.api.client import MovideskClient
from src.utils.logger import get_logger

logger = get_logger()
settings = get_settings()
client = MovideskClient()

print("\n" + "="*60)
print("BUSCA: Tickets com SLA vencido (data no passado)")
print("="*60 + "\n")

# Buscar TODOS os tickets do agente (limite maior)
tickets = client.get_tickets(
    filter_expr=f"owner/email eq '{settings.movidesk_agent_email}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
    top=100,  # Buscar mais tickets
    order_by='slaSolutionDate asc'  # Ordenar por data de SLA (mais antigos primeiro)
)

print(f"Total de tickets abertos: {len(tickets)}\n")

now = datetime.now()
print(f"⏰ Hora atual: {now}\n")

overdue_tickets = []

for ticket in tickets:
    if ticket.slaSolutionDate:
        # Remove timezone if present para comparação simples
        sla_date = ticket.slaSolutionDate
        if sla_date.tzinfo:
            sla_date = sla_date.replace(tzinfo=None)
        
        if sla_date < now:
            overdue_tickets.append((ticket, sla_date))
            print(f"🔴 Ticket #{ticket.ticket_number}: {ticket.subject[:50]}...")
            print(f"   SLA: {sla_date}")
            print(f"   Vencido há: {(now - sla_date).total_seconds() / 3600:.1f} horas")
            print()

print("=" * 60)
if overdue_tickets:
    print(f"✅ ENCONTRADOS {len(overdue_tickets)} TICKETS VENCIDOS!")
else:
    print("❌ Nenhum ticket vencido encontrado")
    print("   (todos os SLAs são para datas futuras)")
print("=" * 60)
