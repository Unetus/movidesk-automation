"""Email notification system."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime

from ..api.models import Ticket
from ..config import get_settings, get_config
from ..utils.logger import get_logger


class EmailNotifierError(Exception):
    """Email notification error."""
    pass


class EmailNotifier:
    """
    Send email notifications for tickets.
    
    Features:
    - HTML email templates
    - Batch notifications
    - SMTP connection management
    """
    
    def __init__(self):
        """Initialize email notifier."""
        self.settings = get_settings()
        self.config = get_config()
        self.logger = get_logger()
        
        # Email config
        self.email_config = self.config.notifications.get('email', {})
        self.enabled = self.settings.email_enabled and self.email_config.get('enabled', True)
        
        if not self.enabled:
            self.logger.info("Email notifications are disabled")
    
    def send_ticket_notification(
        self,
        ticket: Ticket,
        summary: Optional[str] = None
    ) -> bool:
        """
        Send notification for a single ticket.
        
        Args:
            ticket: Ticket to notify about
            summary: AI-generated summary (optional)
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            subject = f"[Movidesk] Ticket #{ticket.ticket_number}: {ticket.subject}"
            html_body = self._format_single_ticket_html(ticket, summary)
            
            self._send_email(
                to=self.settings.email_to,
                subject=subject,
                html_body=html_body
            )
            
            self.logger.info(f"Sent notification for ticket {ticket.id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending notification for ticket {ticket.id}: {e}")
            return False
    
    def send_batch_notification(
        self,
        tickets_with_summaries: List[tuple[Ticket, Optional[str]]]
    ) -> bool:
        """
        Send batch notification for multiple tickets.
        
        Args:
            tickets_with_summaries: List of (ticket, summary) tuples
        
        Returns:
            True if sent successfully
        """
        if not self.enabled or not tickets_with_summaries:
            return False
        
        try:
            count = len(tickets_with_summaries)
            subject_template = self.email_config.get(
                'subject_template',
                '[Movidesk] {count} ticket(s) requer(em) atenção'
            )
            subject = subject_template.replace('{count}', str(count))
            
            html_body = self._format_batch_tickets_html(tickets_with_summaries)
            
            self._send_email(
                to=self.settings.email_to,
                subject=subject,
                html_body=html_body
            )
            
            self.logger.info(f"Sent batch notification for {count} tickets")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending batch notification: {e}")
            return False
    
    def _send_email(self, to: str, subject: str, html_body: str) -> None:
        """
        Send email via SMTP.
        
        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML body content
        """
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = self.settings.email_from
        msg['To'] = to
        msg['Subject'] = subject
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Attach HTML
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send via SMTP
        try:
            with smtplib.SMTP(
                self.settings.email_smtp_server,
                self.settings.email_smtp_port,
                timeout=30
            ) as server:
                server.starttls()
                server.login(self.settings.email_from, self.settings.email_password)
                server.send_message(msg)
                self.logger.debug(f"Email sent to {to}")
        
        except smtplib.SMTPException as e:
            raise EmailNotifierError(f"SMTP error: {e}")
        except Exception as e:
            raise EmailNotifierError(f"Email send error: {e}")
    
    def _format_single_ticket_html(
        self,
        ticket: Ticket,
        summary: Optional[str] = None
    ) -> str:
        """Format HTML for single ticket notification."""
        urgency_color = self._get_urgency_color(ticket.urgency)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{ 
            max-width: 650px; 
            margin: 20px auto; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{ 
            background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
            color: white; 
            padding: 25px 20px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{ 
            padding: 25px; 
        }}
        .ticket-info {{ 
            background: #f9fafb; 
            padding: 20px; 
            border-radius: 6px; 
            margin: 15px 0;
            border: 1px solid #e5e7eb;
        }}
        .ticket-info p {{
            margin: 10px 0;
            font-size: 14px;
        }}
        .label {{ 
            font-weight: 600; 
            color: #4b5563;
            display: inline-block;
            min-width: 140px;
        }}
        .urgency {{ 
            display: inline-block; 
            padding: 6px 12px; 
            border-radius: 4px; 
            color: white; 
            background: {urgency_color};
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        .summary {{ 
            background: linear-gradient(to right, #fffbeb 0%, #fef3c7 100%);
            padding: 15px 18px; 
            border-left: 5px solid #f59e0b; 
            margin: 20px 0;
            border-radius: 6px; 
            font-size: 14px; 
            line-height: 1.9;
            box-shadow: 0 2px 5px rgba(245,158,11,0.15);
        }}
        .summary strong {{
            color: #92400e;
        }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background: #0066cc; 
            color: white !important; 
            text-decoration: none; 
            border-radius: 6px; 
            margin-top: 20px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 2px 4px rgba(0,102,204,0.3);
            transition: background 0.3s;
        }}
        .button:hover {{
            background: #0052a3;
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280; 
            font-size: 12px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎫 Novo Ticket Movidesk</h2>
        </div>
        <div class="content">
            <div class="ticket-info">
                <p><span class="label">Protocolo:</span> #{ticket.ticket_number}</p>
                <p><span class="label">Assunto:</span> {ticket.subject or 'Sem assunto'}</p>
                <p><span class="label">Cliente:</span> {ticket.client_name}</p>
                <p><span class="label">Categoria:</span> {ticket.category or 'N/A'}</p>
                <p><span class="label">Status:</span> {ticket.status or 'N/A'}</p>
                <p><span class="label">Urgência:</span> <span class="urgency">{ticket.urgency or 'Normal'}</span></p>
                <p><span class="label">Responsável:</span> {ticket.owner_name}</p>
                <p><span class="label">Última atualização:</span> {self._format_datetime(ticket.lastUpdate)}</p>
            </div>
            
            {self._render_summary_section(summary)}
            
            <a href="{ticket.movidesk_url}" class="button">📋 Ver Ticket no Movidesk</a>
        </div>
        <div class="footer">
            <p>Movidesk Automation System • {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _format_batch_tickets_html(
        self,
        tickets_with_summaries: List[tuple[Ticket, Optional[str]]]
    ) -> str:
        """Format HTML for batch ticket notification."""
        ticket_items = []
        
        for ticket, summary in tickets_with_summaries:
            urgency_color = self._get_urgency_color(ticket.urgency)
            summary_html = self._render_summary_section(summary) if summary else ""
            
            # Adicionar aviso de vencimento de SLA
            overdue_html = ""
            if ticket.is_overdue:
                days = ticket.days_overdue
                sla_info = f" ({ticket.slaAgreement})" if ticket.slaAgreement else ""
                
                overdue_html = f"""
                <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 10px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #991b1b;">⚠️ TICKET COM SLA VENCIDO!</strong><br>
                    <span style="color: #7f1d1d;">Há {days} dia(s) após o prazo{sla_info}</span>
                </div>
                """
            
            item = f"""
            <div class="ticket-card">
                <div class="ticket-header">
                    <h3>#{ticket.ticket_number} - {ticket.subject or 'Sem assunto'}</h3>
                    <span class="urgency" style="background: {urgency_color};">{ticket.urgency or 'Normal'}</span>
                </div>
                <div class="ticket-body">
                    <p><strong>Cliente:</strong> {ticket.client_name}</p>
                    <p><strong>Status:</strong> {ticket.status or 'N/A'}</p>
                    <p><strong>Categoria:</strong> {ticket.category or 'N/A'}</p>
                    <p><strong>Atualizado:</strong> {self._format_datetime(ticket.lastUpdate)}</p>
                    {overdue_html}
                    {summary_html}
                    <a href="{ticket.movidesk_url}" class="button-small">Ver Ticket</a>
                </div>
            </div>
            """
            ticket_items.append(item)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{ 
            max-width: 850px; 
            margin: 0 auto; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{ 
            background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
            color: white; 
            padding: 25px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0 0 8px 0;
            font-size: 26px;
            font-weight: 600;
        }}
        .header p {{
            margin: 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .ticket-card {{ 
            background: white; 
            border: 1px solid #e5e7eb; 
            border-radius: 6px; 
            margin: 20px; 
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: box-shadow 0.3s;
        }}
        .ticket-card:hover {{
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .ticket-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 2px solid #e5e7eb; 
            padding-bottom: 12px; 
            margin-bottom: 15px;
        }}
        .ticket-header h3 {{ 
            margin: 0; 
            color: #0066cc;
            font-size: 18px;
            font-weight: 600;
        }}
        .ticket-body {{
            font-size: 14px;
        }}
        .ticket-body p {{
            margin: 8px 0;
        }}
        .ticket-body strong {{
            color: #4b5563;
            display: inline-block;
            min-width: 100px;
        }}
        .urgency {{ 
            padding: 6px 12px; 
            border-radius: 4px; 
            color: white; 
            font-size: 12px; 
            font-weight: 600;
            white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        .summary {{ 
            background: linear-gradient(to right, #fffbeb 0%, #fef3c7 100%);
            padding: 14px 16px; 
            border-left: 5px solid #f59e0b; 
            margin: 14px 0;
            border-radius: 6px; 
            font-size: 14px;
            line-height: 1.9;
            box-shadow: 0 2px 5px rgba(245,158,11,0.15);
        }}
        .summary strong {{
            color: #92400e;
        }}
        .button-small {{ 
            display: inline-block; 
            padding: 10px 18px; 
            background: #0066cc; 
            color: white !important; 
            text-decoration: none; 
            border-radius: 5px; 
            margin-top: 12px; 
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,102,204,0.3);
            transition: background 0.3s;
        }}
        .button-small:hover {{
            background: #0052a3;
        }}
        .footer {{ 
            text-align: center; 
            margin: 25px 20px 20px; 
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280; 
            font-size: 12px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎫 {len(tickets_with_summaries)} Ticket(s) Requer(em) Atenção</h2>
            <p>Movidesk - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        {''.join(ticket_items)}
        
        <div class="footer">
            <p>Movidesk Automation System</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _render_summary_section(self, summary: Optional[str]) -> str:
        """Render AI summary section if available."""
        if not summary:
            return ""
        
        # Processar formatação do resumo
        formatted_summary = summary.strip()
        
        # Remover possíveis asteriscos de markdown que a IA poder retornar
        import re
        # Remover negrito markdown (**texto** ou __texto__)
        formatted_summary = re.sub(r'\*\*([^*]+)\*\*', r'\1', formatted_summary)
        formatted_summary = re.sub(r'__([^_]+)__', r'\1', formatted_summary)
        # Remover itálico markdown (*texto* ou _texto_)
        formatted_summary = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', formatted_summary)
        formatted_summary = re.sub(r'(?<!_)_(?!_)([^_]+)_(?!_)', r'\1', formatted_summary)
        
        # Converter quebras de linha em <br>
        formatted_summary = formatted_summary.replace('\n', '<br>')
        
        # Destacar seções (deixar em negrito)
        sections = [
            'PROBLEMA PRINCIPAL:',
            'DETALHES RELEVANTES:',
            'AÇÕES REALIZADAS:',
            'PRÓXIMOS PASSOS:',
            'Unidade:',
            'Equipamento:',
            'Erro:'
        ]
        
        for section in sections:
            if section in formatted_summary:
                formatted_summary = formatted_summary.replace(
                    section,
                    f'<strong style="color: #0066cc;">{section}</strong>'
                )
        
        # Adicionar espaçamento entre seções principais
        formatted_summary = formatted_summary.replace(
            '<br><strong style="color: #0066cc;">PROBLEMA',
            '<br><br><strong style="color: #0066cc;">PROBLEMA'
        )
        formatted_summary = formatted_summary.replace(
            '<br><strong style="color: #0066cc;">DETALHES',
            '<br><br><strong style="color: #0066cc;">DETALHES'
        )
        formatted_summary = formatted_summary.replace(
            '<br><strong style="color: #0066cc;">AÇÕES',
            '<br><br><strong style="color: #0066cc;">AÇÕES'
        )
        formatted_summary = formatted_summary.replace(
            '<br><strong style="color: #0066cc;">PRÓXIMOS',
            '<br><br><strong style="color: #0066cc;">PRÓXIMOS'
        )
        
        # Destacar bullet points com indentação
        formatted_summary = formatted_summary.replace(
            '<br>- ',
            '<br>&nbsp;&nbsp;&nbsp;&nbsp;• '
        )
        
        return f"""
        <div class="summary">
            <strong style="font-size: 15px; color: #0066cc;">🤖 Resumo IA:</strong>
            <div style="margin-top: 12px; line-height: 2.0; color: #1f2937;">{formatted_summary}</div>
        </div>
        """
    
    def _get_urgency_color(self, urgency: Optional[str]) -> str:
        """Get color for urgency level."""
        if not urgency:
            return "#6c757d"  # Gray
        
        urgency_lower = urgency.lower()
        colors = {
            "critical": "#dc3545",  # Red
            "urgent": "#fd7e14",    # Orange
            "high": "#ffc107",      # Yellow
            "medium": "#17a2b8",    # Cyan
            "low": "#28a745"        # Green
        }
        
        for key, color in colors.items():
            if key in urgency_lower:
                return color
        
        return "#6c757d"  # Default gray
    
    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "N/A"
        return dt.strftime("%d/%m/%Y %H:%M")
    
    def send_raw_notification(self, subject: str, body: str) -> bool:
        """
        Send plain text notification (for reports).
        
        Args:
            subject: Email subject
            body: Plain text body
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            self.logger.info("Email notifications disabled, skipping")
            return False
        
        try:
            # Convert plain text to simple HTML with formatting
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: 'Courier New', Courier, monospace; 
            line-height: 1.6; 
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre>{body}</pre>
    </div>
</body>
</html>
"""
            self._send_email(
                to=self.settings.email_to,
                subject=subject,
                html_body=html_body
            )
            self.logger.info(f"Sent raw notification: {subject}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending raw notification: {e}")
            return False
    
    def send_html_notification(self, subject: str, html_body: str) -> bool:
        """
        Send HTML notification (for styled reports).
        
        Args:
            subject: Email subject
            html_body: HTML body content
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            self.logger.info("Email notifications disabled, skipping")
            return False
        
        try:
            self._send_email(
                to=self.settings.email_to,
                subject=subject,
                html_body=html_body
            )
            self.logger.info(f"Sent HTML notification: {subject}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending HTML notification: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful
        """
        try:
            with smtplib.SMTP(
                self.settings.email_smtp_server,
                self.settings.email_smtp_port,
                timeout=10
            ) as server:
                server.starttls()
                server.login(self.settings.email_from, self.settings.email_password)
                self.logger.info("SMTP connection test successful")
                return True
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
