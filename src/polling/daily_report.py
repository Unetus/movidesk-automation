"""Daily report generator for tickets with AI summaries."""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pytz
import time

from ..api import MovideskClient, Ticket
from ..notifications.email_notifier import EmailNotifier
from ..processing.summarizer import TicketSummarizer
from ..config import get_settings
from ..utils.logger import get_logger
from ..database import DatabaseRepository, Report, ReportTicket, AISummary


class DailyReportGenerator:
    """
    Generates comprehensive daily reports for tickets with AI-powered summaries.
    
    Features:
    - New tickets (last 24h)
    - Overdue tickets (SLA expired)
    - Tickets expiring soon (next 2 days)
    - AI summaries with SQLite caching (60-80% token savings!)
    - All timestamps converted to Brazil timezone (BRT/UTC-3)
    - Smart rate limiting to respect API and token quotas
    - Historical data storage for analytics
    - Multi-agent support (v2.0)
    """
    
    def __init__(self, agent_email: Optional[str] = None):
        """
        Initialize report generator.
        
        Args:
            agent_email: Email of the agent to generate report for.
                        If None, uses MOVIDESK_AGENT_EMAIL from settings (backward compatibility).
        """
        self.settings = get_settings()
        self.logger = get_logger()
        self.api_client = MovideskClient()
        self.notifier = EmailNotifier()
        self.summarizer = TicketSummarizer()
        self.db = DatabaseRepository()
        
        # Agent email (supports multi-agent mode)
        self.agent_email = agent_email or self.settings.agent_emails_list[0]
        
        self.logger.info(f"[INIT] DailyReportGenerator inicializado para agente: {self.agent_email}")
        
        # Timezone configuration
        self.utc_tz = pytz.UTC
        self.brt_tz = pytz.timezone('America/Sao_Paulo')
        
        # Batch processing configuration
        self.batch_size = 8  # Process 8 tickets per batch (safe for token limits)
        self.batch_delay = 2  # Seconds between batches
    
    def utc_to_brt(self, dt: Optional[datetime]) -> Optional[datetime]:
        """
        Convert UTC datetime to Brazil timezone.
        
        Args:
            dt: Datetime to convert (assumed UTC if no timezone)
        
        Returns:
            Datetime in BRT timezone
        """
        if dt is None:
            return None
        
        # Ensure datetime has timezone info
        if dt.tzinfo is None:
            dt = self.utc_tz.localize(dt)
        
        # Convert to BRT
        return dt.astimezone(self.brt_tz)
    
    def format_datetime_brt(self, dt: Optional[datetime]) -> str:
        """
        Format datetime in Brazil timezone for display.
        
        Args:
            dt: Datetime to format
        
        Returns:
            Formatted string (DD/MM/YYYY HH:MM)
        """
        if dt is None:
            return "N/A"
        
        dt_brt = self.utc_to_brt(dt)
        return dt_brt.strftime("%d/%m/%Y %H:%M")
    
    def _get_or_generate_summary(self, ticket: Ticket) -> str:
        """
        Get AI summary from cache or generate new one.
        
        Uses SQLite cache for token savings - checks cache first,
        generates only if cache miss or too old (>7 days).
        
        Args:
            ticket: Ticket to summarize
        
        Returns:
            AI summary text
        """
        # Check cache first
        cached_summary = self.db.get_ai_summary(ticket.id)
        if cached_summary:
            self.logger.debug(f"      ♻️  Using cached summary for #{ticket.ticket_number}")
            return cached_summary.summary
        
        # Cache miss - generate new summary
        try:
            summary_text = self.summarizer.summarize_ticket(ticket)
            if not summary_text:
                return "⚠️ Resumo não disponível"
            
            # Get model name from summarizer config
            model_name = self.summarizer.summarization_config.get('model', 'llama-3.3-70b-versatile')
            max_tokens = self.summarizer.summarization_config.get('max_tokens', 150)
            
            # Save to cache
            ai_summary = AISummary(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                subject=ticket.subject,
                summary=summary_text,
                model_used=model_name,
                tokens_used=max_tokens,  # Approximate (max_tokens setting)
                generated_at=datetime.now(),
                last_used_at=datetime.now(),
                use_count=0
            )
            self.db.save_ai_summary(ai_summary)
            self.logger.debug(f"      ✓ Generated + cached summary for #{ticket.ticket_number}")
            
            return summary_text
        
        except Exception as e:
            self.logger.error(f"      ❌ Error summarizing ticket #{ticket.ticket_number}: {e}")
            return "❌ Erro ao gerar resumo"
    
    def _summarize_tickets_in_batches(self, tickets: List[Ticket]) -> Dict[str, str]:
        """
        Generate AI summaries for tickets in batches to respect API/token limits.
        
        Uses SQLite cache to avoid regenerating summaries (60-80% token savings!).
        
        Args:
            tickets: List of tickets to summarize
        
        Returns:
            Dictionary mapping ticket_id -> summary
        """
        if not tickets:
            return {}
        
        summaries = {}
        total_tickets = len(tickets)
        cache_hits = 0
        
        self.logger.info(f"🤖 Gerando/buscando resumos de IA para {total_tickets} tickets...")
        self.logger.info(f"   Processando em lotes de {self.batch_size} tickets")
        
        # Process in batches
        for i in range(0, total_tickets, self.batch_size):
            batch = tickets[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_tickets + self.batch_size - 1) // self.batch_size
            
            self.logger.info(f"   📦 Lote {batch_num}/{total_batches} ({len(batch)} tickets)...")
            
            # Summarize each ticket in batch (with cache check)
            for ticket in batch:
                # Check if we got a cached summary
                cached = self.db.get_ai_summary(ticket.id)
                if cached:
                    cache_hits += 1
                
                summary = self._get_or_generate_summary(ticket)
                summaries[ticket.id] = summary
            
            # Delay between batches to respect rate limits (except for last batch)
            if i + self.batch_size < total_tickets:
                self.logger.debug(f"   ⏱️  Aguardando {self.batch_delay}s antes do próximo lote...")
                time.sleep(self.batch_delay)
        
        success_count = sum(1 for s in summaries.values() if not s.startswith('⚠️') and not s.startswith('❌'))
        cache_rate = (cache_hits / total_tickets * 100) if total_tickets > 0 else 0
        self.logger.info(f"   ✅ {success_count}/{total_tickets} resumos obtidos com sucesso")
        self.logger.info(f"   ♻️  Cache: {cache_hits}/{total_tickets} hits ({cache_rate:.1f}% reuso)")
        
        return summaries
    
    def get_new_tickets(self, hours: int = 24) -> List[Ticket]:
        """
        Get tickets created in the last N hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of tickets created recently
        """
        self.logger.info(f"📅 Fetching tickets created in last {hours} hours...")
        
        # Calculate cutoff time in UTC
        now_utc = datetime.now(self.utc_tz)
        cutoff_utc = now_utc - timedelta(hours=hours)
        
        # Fetch all open tickets (limit to avoid API overload)
        tickets = self.api_client.get_tickets(
            filter_expr=f"owner/email eq '{self.agent_email}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
            top=50,  # Limit to 50 to respect API quotas
            order_by='createdDate desc'
        )
        
        # Filter by creation date
        new_tickets = []
        for ticket in tickets:
            if ticket.createdDate:
                # Convert to UTC for comparison
                created_dt = ticket.createdDate
                if created_dt.tzinfo is None:
                    created_dt = self.utc_tz.localize(created_dt)
                else:
                    created_dt = created_dt.astimezone(self.utc_tz)
                
                if created_dt >= cutoff_utc:
                    new_tickets.append(ticket)
        
        self.logger.info(f"   Found {len(new_tickets)} new tickets")
        return new_tickets
    
    def get_overdue_tickets(self) -> List[Ticket]:
        """
        Get tickets with expired SLA.
        
        Returns:
            List of overdue tickets
        """
        self.logger.info("🔴 Fetching overdue tickets...")
        
        # Use existing method from API client (already respects rate limits)
        overdue = self.api_client.get_overdue_tickets_for_agent(
            agent_email=self.agent_email,
            limit=50  # Limit to respect API
        )
        
        self.logger.info(f"   Found {len(overdue)} overdue tickets")
        return overdue
    
    def get_expiring_soon_tickets(self, days: int = 2) -> List[Tuple[Ticket, float]]:
        """
        Get tickets expiring in the next N days.
        
        Args:
            days: Number of days to look ahead
        
        Returns:
            List of (ticket, hours_until_expiry) tuples
        """
        self.logger.info(f"⚠️  Fetching tickets expiring in next {days} days...")
        
        now_utc = datetime.now(self.utc_tz)
        cutoff_utc = now_utc + timedelta(days=days)
        
        # Fetch all open tickets (reuse from get_new_tickets to save API calls)
        tickets = self.api_client.get_tickets(
            filter_expr=f"owner/email eq '{self.agent_email}' and baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
            top=50
        )
        
        expiring_soon = []
        for ticket in tickets:
            if ticket.slaSolutionDate and not ticket.is_overdue:
                # Convert SLA to UTC for comparison
                sla_utc = self.utc_tz.localize(ticket.slaSolutionDate) if ticket.slaSolutionDate.tzinfo is None else ticket.slaSolutionDate
                
                if now_utc < sla_utc <= cutoff_utc:
                    hours_until = (sla_utc - now_utc).total_seconds() / 3600
                    expiring_soon.append((ticket, hours_until))
        
        # Sort by expiry time (most urgent first)
        expiring_soon.sort(key=lambda x: x[1])
        
        self.logger.info(f"   Found {len(expiring_soon)} tickets expiring soon")
        return expiring_soon
    
    def generate_report(self) -> Dict[str, any]:
        """
        Generate complete daily report with AI summaries ONLY for new and overdue tickets.
        
        Expiring soon tickets show raw data only (to save API tokens).
        
        Returns:
            Dictionary containing report sections and summaries
        """
        self.logger.info("\n" + "="*70)
        self.logger.info("📊 GERANDO RELATÓRIO DIÁRIO")
        self.logger.info("="*70)
        
        # Get current time in BRT
        now_brt = datetime.now(self.brt_tz)
        
        # Fetch all sections (optimized to minimize API calls)
        new_tickets = self.get_new_tickets(hours=24)
        overdue_tickets = self.get_overdue_tickets()
        expiring_soon = self.get_expiring_soon_tickets(days=2)
        
        # Collect tickets that NEED AI summaries (new + overdue only)
        # Expiring soon tickets will be shown with raw data only
        tickets_for_summarization = new_tickets + overdue_tickets
        
        # Generate AI summaries ONLY for new and overdue tickets
        summaries = self._summarize_tickets_in_batches(tickets_for_summarization)
        
        # Build report
        report = {
            'generated_at': now_brt,
            'new_tickets': new_tickets,
            'overdue_tickets': overdue_tickets,
            'expiring_soon': expiring_soon,
            'summaries': summaries,
            'statistics': {
                'total_new': len(new_tickets),
                'total_overdue': len(overdue_tickets),
                'total_expiring': len(expiring_soon),
                'total_summarized': len(tickets_for_summarization)
            }
        }
        
        self.logger.info("\n📈 Resumo:")
        self.logger.info(f"   🆕 Novos tickets (24h): {report['statistics']['total_new']}")
        self.logger.info(f"   🔴 Tickets vencidos: {report['statistics']['total_overdue']}")
        self.logger.info(f"   ⚠️  Vencendo em 2 dias: {report['statistics']['total_expiring']}")
        self.logger.info(f"   🤖 Tickets com resumo de IA (novos + vencidos): {report['statistics']['total_summarized']}")
        self.logger.info(f"   📊 Tickets sem resumo (vencendo em breve): {report['statistics']['total_expiring']}")
        self.logger.info("="*70 + "\n")
        
        return report
    
    def format_report_text(self, report: Dict[str, any]) -> str:
        """
        Format report as plain text with AI summaries for email/display.
        
        Args:
            report: Report dictionary from generate_report()
        
        Returns:
            Formatted text report
        """
        lines = []
        summaries = report.get('summaries', {})
        
        # Header
        lines.append("="*70)
        lines.append("[CHART] RELATORIO DIARIO DE TICKETS")
        lines.append("="*70)
        lines.append(f"Gerado em: {report['generated_at'].strftime('%d/%m/%Y às %H:%M')} (Horário de Brasília)")
        lines.append(f"Agente: {self.agent_email}")
        lines.append("="*70)
        lines.append("")
        
        # Statistics summary
        stats = report['statistics']
        lines.append("📈 RESUMO GERAL")
        lines.append("-"*70)
        lines.append(f"   🆕 Novos tickets (últimas 24h): {stats['total_new']}")
        lines.append(f"   🔴 Tickets com SLA vencido: {stats['total_overdue']}")
        lines.append(f"   ⚠️  Tickets vencendo (próximos 2 dias): {stats['total_expiring']}")
        lines.append(f"   🤖 Resumos de IA gerados: {stats['total_summarized']}")
        lines.append("")
        
        # Section 1: New Tickets
        lines.append("="*70)
        lines.append("🆕 NOVOS TICKETS (ÚLTIMAS 24 HORAS)")
        lines.append("="*70)
        
        if report['new_tickets']:
            for i, ticket in enumerate(report['new_tickets'], 1):
                lines.append(f"\n{i}. Ticket #{ticket.ticket_number}")
                lines.append(f"   📋 Assunto: {ticket.subject}")
                lines.append(f"   👤 Cliente: {ticket.client_name}")
                lines.append(f"   📊 Status: {ticket.baseStatus} ({ticket.status})")
                lines.append(f"   🎯 Urgência: {ticket.urgency or 'N/A'}")
                lines.append(f"   📅 Criado em: {self.format_datetime_brt(ticket.createdDate)}")
                if ticket.slaSolutionDate:
                    lines.append(f"   ⏰ SLA até: {self.format_datetime_brt(ticket.slaSolutionDate)}")
                
                # Add AI summary
                if ticket.id in summaries:
                    lines.append(f"\n   🤖 Resumo IA:")
                    # Indent summary text
                    summary_lines = summaries[ticket.id].split('\n')
                    for line in summary_lines:
                        lines.append(f"      {line}")
                
                lines.append(f"\n   🔗 {ticket.movidesk_url}")
        else:
            lines.append("\n✅ Nenhum ticket novo nas últimas 24 horas")
        
        lines.append("")
        
        # Section 2: Overdue Tickets
        lines.append("="*70)
        lines.append("🔴 TICKETS COM SLA VENCIDO")
        lines.append("="*70)
        
        if report['overdue_tickets']:
            for i, ticket in enumerate(report['overdue_tickets'], 1):
                lines.append(f"\n{i}. Ticket #{ticket.ticket_number} - ⚠️ VENCIDO!")
                lines.append(f"   📋 Assunto: {ticket.subject}")
                lines.append(f"   👤 Cliente: {ticket.client_name}")
                lines.append(f"   📊 Status: {ticket.baseStatus} ({ticket.status})")
                lines.append(f"   🎯 Urgência: {ticket.urgency or 'N/A'}")
                lines.append(f"   ⏰ SLA era: {self.format_datetime_brt(ticket.slaSolutionDate)}")
                lines.append(f"   🕒 Vencido há: {ticket.days_overdue} dia(s)")
                
                # Add AI summary
                if ticket.id in summaries:
                    lines.append(f"\n   🤖 Resumo IA:")
                    summary_lines = summaries[ticket.id].split('\n')
                    for line in summary_lines:
                        lines.append(f"      {line}")
                
                lines.append(f"\n   🔗 {ticket.movidesk_url}")
        else:
            lines.append("\n✅ Nenhum ticket com SLA vencido no momento!")
        
        lines.append("")
        
        # Section 3: Expiring Soon
        lines.append("="*70)
        lines.append("⚠️  TICKETS VENCENDO NOS PRÓXIMOS 2 DIAS")
        lines.append("="*70)
        
        if report['expiring_soon']:
            for i, (ticket, hours_until) in enumerate(report['expiring_soon'], 1):
                days = int(hours_until // 24)
                remaining_hours = int(hours_until % 24)
                
                lines.append(f"\n{i}. Ticket #{ticket.ticket_number}")
                lines.append(f"   📋 Assunto: {ticket.subject}")
                lines.append(f"   👤 Cliente: {ticket.client_name}")
                lines.append(f"   📊 Status: {ticket.baseStatus} ({ticket.status})")
                lines.append(f"   🎯 Urgência: {ticket.urgency or 'N/A'}")
                lines.append(f"   ⏰ SLA até: {self.format_datetime_brt(ticket.slaSolutionDate)}")
                lines.append(f"   ⏳ Tempo restante: {days} dia(s) e {remaining_hours} hora(s)")
                
                # Note: Resumos de IA são apenas para novos e vencidos (economia de tokens)
                # Tickets vencendo mostram dados brutos apenas
                
                lines.append(f"\n   🔗 {ticket.movidesk_url}")
        else:
            lines.append("\n✅ Nenhum ticket vencendo nos próximos 2 dias")
        
        lines.append("")
        lines.append("="*70)
        lines.append("📧 Relatório gerado automaticamente")
        lines.append("   Resumos de IA: apenas para NOVOS e VENCIDOS (economia de tokens)")
        lines.append("   Tickets vencendo: dados brutos para referência rápida")
        lines.append("   Movidesk Automation | Powered by Groq AI")
        lines.append("="*70)
        
        return "\n".join(lines)
    
    def format_report_html(self, report: Dict[str, any]) -> str:
        """
        Format report as styled HTML with AI summaries for email.
        
        Args:
            report: Report dictionary from generate_report()
        
        Returns:
            Formatted HTML report
        """
        summaries = report.get('summaries', {})
        stats = report['statistics']
        generated_at = report['generated_at'].strftime('%d/%m/%Y às %H:%M')
        
        def render_ticket_card(ticket, category, hours_until=None):
            """Render a single ticket card HTML"""
            summary_html = ""
            if ticket.id in summaries:
                summary_text = summaries[ticket.id]
                summary_html = f"""
                <div class="summary-box">
                    <strong>🤖 Resumo IA:</strong>
                    <p>{summary_text}</p>
                </div>
                """
            
            # Status colors
            urgency_color = {
                'Critical': '#dc2626',
                'High': '#ea580c',
                'Medium': '#eab308',
                'Low': '#16a34a',
            }.get(ticket.urgency, '#6b7280')
            
            # Extra info for expiring tickets
            expiring_info = ""
            if hours_until is not None:
                days = int(hours_until // 24)
                hours = int(hours_until % 24)
                expiring_info = f"<p><strong>⏳ Tempo restante:</strong> {days}d {hours}h</p>"
            
            # Extra info for overdue tickets
            overdue_info = ""
            if ticket.is_overdue:
                overdue_info = f'<p style="color: #dc2626; font-weight: 600;">🚨 Vencido há {ticket.days_overdue} dia(s)</p>'
            
            return f"""
            <div class="ticket-card">
                <div class="ticket-header">
                    <div>
                        <h3>#{ticket.ticket_number}</h3>
                        <p class="subject">{ticket.subject or 'Sem assunto'}</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="urgency-badge" style="background-color: {urgency_color};">
                            {ticket.urgency or 'Normal'}
                        </span>
                    </div>
                </div>
                <div class="ticket-body">
                    <p><strong>👤 Cliente:</strong> {ticket.client_name}</p>
                    <p><strong>📊 Status:</strong> {ticket.status or 'N/A'}</p>
                    <p><strong>📂 Categoria:</strong> {ticket.category or 'N/A'}</p>
                    {overdue_info}
                    {expiring_info}
                    <p><strong>⏰ SLA:</strong> {self.format_datetime_brt(ticket.slaSolutionDate)}</p>
                    {summary_html}
                    <a href="{ticket.movidesk_url}" class="ticket-link" target="_blank">Ver no Movidesk →</a>
                </div>
            </div>
            """
        
        # Build section HTML
        new_tickets_html = ""
        if report['new_tickets']:
            for ticket in report['new_tickets']:
                new_tickets_html += render_ticket_card(ticket, 'new')
        else:
            new_tickets_html = '<div class="empty-state">✅ Nenhum ticket novo</div>'
        
        overdue_tickets_html = ""
        if report['overdue_tickets']:
            for ticket in report['overdue_tickets']:
                overdue_tickets_html += render_ticket_card(ticket, 'overdue')
        else:
            overdue_tickets_html = '<div class="empty-state">✅ Nenhum ticket vencido</div>'
        
        expiring_tickets_html = ""
        if report['expiring_soon']:
            for ticket, hours_until in report['expiring_soon']:
                expiring_tickets_html += render_ticket_card(ticket, 'expiring', hours_until)
        else:
            expiring_tickets_html = '<div class="empty-state">✅ Nenhum ticket vencendo em breve</div>'
        
        # Complete HTML template
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Diário de Tickets</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        
        .header p {{
            font-size: 14px;
            opacity: 0.95;
            margin: 4px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 15px;
            padding: 30px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .stat-box {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }}
        
        .stat-number {{
            font-size: 28px;
            font-weight: 700;
            color: #0066cc;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .section {{
            padding: 30px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .section:last-of-type {{
            border-bottom: none;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid #0066cc;
            display: inline-block;
        }}
        
        .section-new .section-title {{
            border-color: #16a34a;
            color: #16a34a;
        }}
        
        .section-overdue .section-title {{
            border-color: #dc2626;
            color: #dc2626;
        }}
        
        .section-expiring .section-title {{
            border-color: #ea580c;
            color: #ea580c;
        }}
        
        .ticket-card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .ticket-card:hover {{
            border-color: #0066cc;
            box-shadow: 0 4px 12px rgba(0,102,204,0.15);
        }}
        
        .ticket-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 16px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .ticket-header h3 {{
            font-size: 18px;
            color: #0066cc;
            margin-bottom: 4px;
        }}
        
        .ticket-header p.subject {{
            font-size: 14px;
            color: #374151;
            font-weight: 500;
            margin: 0;
        }}
        
        .urgency-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .ticket-body {{
            padding: 16px;
            font-size: 14px;
            line-height: 1.8;
        }}
        
        .ticket-body p {{
            margin: 8px 0;
        }}
        
        .ticket-body strong {{
            color: #1f2937;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #fef3c7 0%, #fce7aa 100%);
            border-left: 4px solid #ea580c;
            padding: 12px 14px;
            border-radius: 6px;
            margin-top: 12px;
            font-size: 13px;
            line-height: 1.6;
        }}
        
        .summary-box strong {{
            color: #92400e;
        }}
        
        .summary-box p {{
            margin: 8px 0 0 0;
            color: #78350f;
        }}
        
        .ticket-link {{
            display: inline-block;
            margin-top: 12px;
            padding: 8px 16px;
            background: #0066cc;
            color: white !important;
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            transition: background 0.3s;
        }}
        
        .ticket-link:hover {{
            background: #0052a3;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
            font-style: italic;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #f3f4f6;
            text-align: center;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
            
            .ticket-header {{
                flex-direction: column;
            }}
            
            .urgency-badge {{
                margin-top: 10px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                padding: 25px 20px;
            }}
            
            .section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório Diário de Tickets</h1>
            <p>Gerado em {generated_at}</p>
            <p>Agente: {self.agent_email}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{stats['total_new']}</div>
                <div class="stat-label">🆕 Novos (24h)</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #dc2626;">{stats['total_overdue']}</div>
                <div class="stat-label">🔴 Vencidos</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #ea580c;">{stats['total_expiring']}</div>
                <div class="stat-label">⚠️  Vencendo</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #7c3aed;">{stats['total_summarized']}</div>
                <div class="stat-label">🤖 Resumos IA</div>
            </div>
        </div>
        
        <div class="section section-new">
            <h2 class="section-title">🆕 Novos Tickets (Últimas 24 Horas)</h2>
            <div style="margin-top: 20px;">
                {new_tickets_html}
            </div>
        </div>
        
        <div class="section section-overdue">
            <h2 class="section-title">🔴 Tickets com SLA Vencido</h2>
            <div style="margin-top: 20px;">
                {overdue_tickets_html}
            </div>
        </div>
        
        <div class="section section-expiring">
            <h2 class="section-title">⚠️ Tickets Vencendo (Próximos 2 Dias)</h2>
            <div style="margin-top: 20px;">
                {expiring_tickets_html}
            </div>
        </div>
        
        <div class="footer">
            <p>📧 Relatório gerado automaticamente com resumos de IA</p>
            <p>Movidesk Automation • Powered by Groq AI</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_daily_report(self) -> None:
        """Generate and send comprehensive daily report with AI summaries via email (HTML format)."""
        start_time = time.time()
        
        try:
            # Generate report with AI summaries
            self.logger.info("=" * 60)
            self.logger.info("📊 GERAÇÃO DE RELATÓRIO DIÁRIO")
            self.logger.info("=" * 60)
            
            report = self.generate_report()
            
            # Format as HTML (styled for email)
            report_html = self.format_report_html(report)
            
            # Also print text version to console
            report_text = self.format_report_text(report)
            print("\n" + report_text + "\n")
            
            # Get comparison with yesterday
            comparison = self.db.get_comparison_with_yesterday(self.agent_email)
            
            # Save report to database
            self.logger.info("[DB] Salvando relatório no banco de dados...")
            report_record = Report(
                generated_at=report['generated_at'],
                agent_email=self.agent_email,
                total_new=report['statistics']['total_new'],
                total_overdue=report['statistics']['total_overdue'],
                total_expiring=report['statistics']['total_expiring'],
                total_summarized=report['statistics']['total_summarized'],
                email_sent=False,  # Will update after sending
                email_subject=f"Relatório Diário - Tickets do dia ({report['generated_at'].strftime('%d/%m/%Y')})",
                execution_time_seconds=None  # Will update at end
            )
            report_id = self.db.create_report(report_record)
            self.logger.info(f"   [OK] Relatório salvo com ID {report_id}")
            
            # Save ticket snapshots to database
            self.logger.info("[DB] Salvando tickets no banco de dados...")
            tickets_saved = 0
            
            # Save new tickets
            for ticket in report['new_tickets']:
                ticket_record = ReportTicket(
                    report_id=report_id,
                    ticket_id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    subject=ticket.subject,
                    client_name=ticket.client_name,
                    status=ticket.status,
                    base_status=ticket.baseStatus,
                    urgency=ticket.urgency,
                    category=ticket.category,
                    created_date=ticket.createdDate,
                    last_update=ticket.lastUpdate,
                    sla_solution_date=ticket.slaSolutionDate,
                    is_overdue=ticket.is_overdue,
                    days_overdue=ticket.days_overdue,
                    section='new',
                    movidesk_url=f"https://app.movidesk.com/Ticket/Edit/{ticket.id}"
                )
                self.db.add_ticket_to_report(ticket_record)
                tickets_saved += 1
            
            # Save overdue tickets
            for ticket in report['overdue_tickets']:
                ticket_record = ReportTicket(
                    report_id=report_id,
                    ticket_id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    subject=ticket.subject,
                    client_name=ticket.client_name,
                    status=ticket.status,
                    base_status=ticket.baseStatus,
                    urgency=ticket.urgency,
                    category=ticket.category,
                    created_date=ticket.createdDate,
                    last_update=ticket.lastUpdate,
                    sla_solution_date=ticket.slaSolutionDate,
                    is_overdue=ticket.is_overdue,
                    days_overdue=ticket.days_overdue,
                    section='overdue',
                    movidesk_url=f"https://app.movidesk.com/Ticket/Edit/{ticket.id}"
                )
                self.db.add_ticket_to_report(ticket_record)
                tickets_saved += 1
            
            # Save expiring tickets
            for ticket, hours_until in report['expiring_soon']:
                ticket_record = ReportTicket(
                    report_id=report_id,
                    ticket_id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    subject=ticket.subject,
                    client_name=ticket.client_name,
                    status=ticket.status,
                    base_status=ticket.baseStatus,
                    urgency=ticket.urgency,
                    category=ticket.category,
                    created_date=ticket.createdDate,
                    last_update=ticket.lastUpdate,
                    sla_solution_date=ticket.slaSolutionDate,
                    is_overdue=ticket.is_overdue,
                    days_overdue=ticket.days_overdue,
                    section='expiring',
                    movidesk_url=f"https://app.movidesk.com/Ticket/Edit/{ticket.id}"
                )
                self.db.add_ticket_to_report(ticket_record)
                tickets_saved += 1
            
            self.logger.info(f"   [OK] {tickets_saved} tickets salvos no relatório")
            
            # Log comparison stats
            if comparison and comparison.get('yesterday'):
                self.logger.info("[STATS] Comparacao com ontem:")
                self.logger.info(f"   Novos: {comparison['today'].get('new_tickets', 0)} (ontem: {comparison['yesterday'].get('new_tickets', 0)}, diff: {comparison['diff_new']:+d})")
                self.logger.info(f"   Vencidos: {comparison['today'].get('overdue_tickets', 0)} (ontem: {comparison['yesterday'].get('overdue_tickets', 0)}, diff: {comparison['diff_overdue']:+d})")
            
            # Send via email with HTML formatting
            generated_date = report['generated_at'].strftime('%d/%m/%Y')
            subject = f"Relatório Diário - Tickets do dia ({generated_date})"
            
            self.logger.info(f"[EMAIL] [START] Enviando relatório para {self.agent_email} (formato HTML)...")
            email_result = self.notifier.send_html_notification(
                subject=subject,
                html_body=report_html,
                to=self.agent_email  # Send to agent's own email
            )
            self.logger.info(f"[EMAIL] [END] Resultado envio: {email_result}")
            
            # Update report as sent
            self.db.update_report(report_id, email_sent=True)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            self.db.update_report(report_id, execution_time=execution_time)
            
            # Log cache statistics
            cache_stats = self.db.get_summary_stats()
            self.logger.info("=" * 60)
            self.logger.info("[CACHE] CACHE STATISTICS")
            self.logger.info("=" * 60)
            self.logger.info(f"   Total resumos em cache: {cache_stats.get('total_summaries', 0)}")
            self.logger.info(f"   Total tokens usados: {cache_stats.get('total_tokens_used', 0)}")
            self.logger.info(f"   Total reusos: {cache_stats.get('total_reuses', 0)}")
            self.logger.info(f"   Média reusos/resumo: {cache_stats.get('avg_reuses_per_summary', 0):.1f}")
            
            self.logger.info("=" * 60)
            self.logger.info(f"[OK] Relatório enviado com sucesso! (tempo: {execution_time:.1f}s)")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erro ao gerar/enviar relatorio: {e}", exc_info=True)
            raise
