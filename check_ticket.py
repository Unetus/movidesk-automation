#!/usr/bin/env python3
"""Check specific ticket details."""

import sys
sys.path.append('.')

from datetime import datetime
import pytz
from src.config import get_settings
from src.api.client import MovideskClient

settings = get_settings()
client = MovideskClient()

# Ticket ID from HTML inspection
ticket_id = 60271

print("\n" + "="*60)
print(f"DETALHES DO TICKET #{ticket_id}")
print("="*60 + "\n")

# Fetch single ticket
tickets = client.get_tickets(
    filter_expr=f"id eq {ticket_id}",
    top=1
)

if tickets:
    ticket = tickets[0]
    
    print(f"Assunto: {ticket.subject}")
    print(f"Status: {ticket.baseStatus} ({ticket.status})")
    print(f"Urgência: {ticket.urgency}")
    print(f"\n📅 Datas:")
    print(f"   Criado em: {ticket.createdDate}")
    print(f"   Última atualização: {ticket.lastUpdate}")
    print(f"   slaSolutionDate (raw): {ticket.slaSolutionDate}")
    
    if ticket.slaSolutionDate:
        # Movidesk retorna em UTC sem timezone marker
        sla_utc = pytz.UTC.localize(ticket.slaSolutionDate) if ticket.slaSolutionDate.tzinfo is None else ticket.slaSolutionDate
        now_utc = datetime.now(pytz.UTC)
        
        # Converter para horário de Brasília para exibição
        br_tz = pytz.timezone('America/Sao_Paulo')
        sla_br = sla_utc.astimezone(br_tz)
        now_br = now_utc.astimezone(br_tz)
        
        print(f"\n⏰ Status do SLA (CORRIGIDO COM UTC):")
        print(f"   === UTC (usado na API) ===")
        print(f"   Agora: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   SLA:   {sla_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        print(f"\n   === Horário Local (BRT/UTC-3) ===")
        print(f"   Agora: {now_br.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   SLA:   {sla_br.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        diff_hours = (now_utc - sla_utc).total_seconds() / 3600
        
        if diff_hours > 0:
            print(f"\n   🔴 VENCIDO há {diff_hours:.1f} horas ({diff_hours * 60:.0f} minutos)")
        else:
            print(f"\n   ✅ DENTRO DO PRAZO (faltam {abs(diff_hours):.1f} horas)")
    else:
        print(f"\n   ⚠️  SEM SLA DEFINIDO")
    
    print(f"\n🔍 Detection Properties (após correção):")
    print(f"   is_overdue: {ticket.is_overdue}")
    print(f"   days_overdue: {ticket.days_overdue}")
    print(f"   effective_due_date: {ticket.effective_due_date}")
else:
    print(f"❌ Ticket #{ticket_id} não encontrado")

print("\n" + "="*60)
