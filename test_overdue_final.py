#!/usr/bin/env python3
"""Find ALL overdue tickets using corrected model properties."""

import sys
sys.path.append('.')

from datetime import datetime
import pytz
from src.config import get_settings
from src.api.client import MovideskClient
from src.utils.logger import get_logger

logger = get_logger()
settings = get_settings()
client = MovideskClient()

print("\n" + "="*70)
print("🔍 BUSCA COMPLETA: Tickets com SLA vencido (usando modelo corrigido)")
print("="*70 + "\n")

# Buscar todos os tickets abertos do agente
tickets = client.get_tickets(
    filter_expr=f"owner/email eq '{settings.movidesk_agent_email}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
    top=100,
    order_by='lastUpdate desc'
)

print(f"📊 Total de tickets abertos: {len(tickets)}\n")

# Usar a hora atual em ambos timezones para referência
now_utc = datetime.now(pytz.UTC)
br_tz = pytz.timezone('America/Sao_Paulo')
now_br = now_utc.astimezone(br_tz)

print(f"⏰ Hora atual:")
print(f"   UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   BRT: {now_br.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()

# Analisar cada ticket usando as properties do modelo
overdue_tickets = []
tickets_with_sla = 0

for ticket in tickets:
    if ticket.slaSolutionDate:
        tickets_with_sla += 1
        
        # Usar a property is_overdue do modelo (já corrigida com UTC!)
        if ticket.is_overdue:
            overdue_tickets.append(ticket)
            
            # Converter SLA para BRT para exibição amigável
            sla_utc = pytz.UTC.localize(ticket.slaSolutionDate) if ticket.slaSolutionDate.tzinfo is None else ticket.slaSolutionDate
            sla_br = sla_utc.astimezone(br_tz)
            
            print(f"🔴 Ticket #{ticket.ticket_number}: {ticket.subject[:60]}...")
            print(f"   Urgência: {ticket.urgency}")
            print(f"   SLA (UTC): {ticket.slaSolutionDate}")
            print(f"   SLA (BRT): {sla_br.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Vencido há: {ticket.days_overdue} dia(s)")
            print(f"   URL: {ticket.movidesk_url}")
            print()

print("="*70)
print(f"📈 RESUMO:")
print(f"   Total de tickets: {len(tickets)}")
print(f"   Com SLA definido: {tickets_with_sla}")
print(f"   🔴 VENCIDOS: {len(overdue_tickets)}")

if overdue_tickets:
    print(f"\n✅ Sistema funcionando! {len(overdue_tickets)} ticket(s) vencido(s) detectado(s)!")
else:
    print(f"\n⚠️  Nenhum ticket vencido encontrado no momento.")

print("="*70 + "\n")
