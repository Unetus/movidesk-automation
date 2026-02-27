"""Main polling engine."""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pytz

from ..api import MovideskClient, Ticket
from ..processing.summarizer import TicketSummarizer
from ..notifications.email_notifier import EmailNotifier
from ..config import get_config, get_settings
from ..utils.logger import get_logger
from .state import StateManager


class TicketPoller:
    """
    Main polling engine for Movidesk tickets.
    
    Features:
    - Fetch latest N tickets for agent
    - Intelligent polling based on business hours
    - Filtering by urgency, status, assignment
    - Batch notifications with AI summaries
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize poller.
        
        Args:
            dry_run: If True, don't send notifications (testing mode)
        """
        self.config = get_config()
        self.settings = get_settings()
        self.logger = get_logger()
        self.dry_run = dry_run
        
        # Components
        self.api_client = MovideskClient()
        self.summarizer = TicketSummarizer()
        self.notifier = EmailNotifier()
        self.state = StateManager(
            self.config.get('database.state_file', './data/state.json')
        )
        
        # Config
        self.polling_config = self.config.polling
        self.filters_config = self.config.filters
        
        if dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no notifications will be sent")
    
    def poll_once(self) -> int:
        """
        Execute one polling cycle.
        
        Returns:
            Number of tickets found
        """
        self.logger.info("=== Starting polling cycle ===")
        
        try:
            # Get latest tickets for the agent
            tickets = self._fetch_tickets()
            
            if not tickets:
                self.logger.info("No tickets found for agent")
                self.state.update_last_poll_time()
                return 0
            
            self.logger.info(f"Found {len(tickets)} ticket(s) - processing all")
            
            # Process all tickets
            tickets_with_summaries = self._process_tickets(tickets)
            
            # Send notifications
            if not self.dry_run:
                self._send_notifications(tickets_with_summaries)
            else:
                self.logger.info(f"DRY RUN: Would send report with {len(tickets_with_summaries)} ticket(s)")
                for ticket, summary in tickets_with_summaries:
                    urgency_icon = self._get_urgency_icon(ticket.urgency)
                    self.logger.info(f"  {urgency_icon} #{ticket.protocol}: {ticket.subject}")
                    if summary:
                        self.logger.info(f"    Summary: {summary[:80]}...")
            
            self.state.update_last_poll_time()
            
            self.logger.info(f"=== Polling cycle complete: {len(tickets)} tickets processed ===")
            return len(tickets)
        
        except Exception as e:
            self.logger.error(f"Error in polling cycle: {e}", exc_info=True)
            return 0
    
    def _fetch_tickets(self) -> List[Ticket]:
        """Fetch latest tickets from Movidesk API."""
        # Get number of tickets to fetch from config (default 5)
        ticket_limit = self.filters_config.get('ticket_limit', 5)
        exclude_closed = self.filters_config.get('exclude_closed', True)
        
        # Use new method to get latest N tickets for agent
        tickets = self.api_client.get_latest_tickets_for_agent(
            agent_email=self.settings.movidesk_agent_email,
            limit=ticket_limit,
            exclude_closed=exclude_closed
        )
        
        return tickets
    
    def fetch_overdue_tickets(self) -> List[Ticket]:
        """Fetch tickets with SLA breach from Movidesk API."""
        self.logger.info("🔴 Fetching tickets with SLA defined...")
        
        tickets = self.api_client.get_overdue_tickets_for_agent(
            agent_email=self.settings.movidesk_agent_email,
            limit=50  # Buscar até 50 tickets com SLA
        )
        
        if tickets:
            self.logger.info(f"⚠️ Found {len(tickets)} ticket(s) with SLA BREACH")
            for ticket in tickets[:5]:  # Log primeiros 5
                days = ticket.days_overdue
                self.logger.warning(
                    f"  🔴 Ticket #{ticket.ticket_number}: {days} day(s) overdue - {ticket.subject[:50]}"
                )
            if len(tickets) > 5:
                self.logger.info(f"  ... and {len(tickets) - 5} more overdue tickets")
        else:
            self.logger.info("✅ No tickets with SLA breach found")
        
        return tickets
    
    def process_overdue_tickets(self) -> int:
        """
        Process tickets with SLA breach and send notifications.
        
        Returns:
            Number of tickets processed
        """
        try:
            self.logger.info("=== Processing tickets with SLA breach ===")
            
            # Fetch tickets with SLA vencido
            tickets = self.fetch_overdue_tickets()
            
            if not tickets:
                self.logger.info("No tickets with SLA breach found - all tickets are within SLA")
                return 0
            
            self.logger.info(f"Processing {len(tickets)} ticket(s) with SLA breach")
            
            # Process tickets and generate summaries
            tickets_with_summaries = self._process_tickets(tickets)
            
            # Send notifications
            self._send_notifications(tickets_with_summaries)
            
            self.logger.info(f"=== Overdue tickets processing complete: {len(tickets)} tickets ===")
            return len(tickets)
        
        except Exception as e:
            self.logger.error(f"Error processing overdue tickets: {e}", exc_info=True)
            return 0
    
    def _process_tickets(
        self,
        tickets: List[Ticket]
    ) -> List[Tuple[Ticket, Optional[str]]]:
        """
        Process tickets and generate summaries.
        
        Args:
            tickets: List of tickets
        
        Returns:
            List of (ticket, summary) tuples
        """
        results = []
        
        for ticket in tickets:
            try:
                # Generate summary
                summary = self.summarizer.summarize_ticket(ticket)
                results.append((ticket, summary))
                
                urgency_icon = self._get_urgency_icon(ticket.urgency)
                self.logger.info(
                    f"Processed {urgency_icon} ticket #{ticket.ticket_number} - "
                    f"{ticket.subject[:50]}..."
                )
            
            except Exception as e:
                self.logger.error(f"Error processing ticket {ticket.id}: {e}")
                # Include without summary
                results.append((ticket, None))
        
        return results
    
    def _send_notifications(
        self,
        tickets_with_summaries: List[Tuple[Ticket, Optional[str]]]
    ) -> None:
        """Send email notifications."""
        if not tickets_with_summaries:
            return
        
        # Always send as batch report
        self.logger.info(f"Sending batch notification for {len(tickets_with_summaries)} tickets")
        self.notifier.send_batch_notification(tickets_with_summaries)
    
    def _get_urgency_icon(self, urgency: Optional[str]) -> str:
        """Get icon for urgency level."""
        if not urgency:
            return "⚪"
        
        urgency_lower = urgency.lower()
        icons = {
            "critical": "🔴",
            "urgent": "🟠",
            "high": "🟡",
            "medium": "🔵",
            "normal": "🟢",
            "low": "⚪"
        }
        
        for key, icon in icons.items():
            if key in urgency_lower:
                return icon
        
        return "⚪"
    
    def is_business_hours(self) -> bool:
        """
        Check if current time is within business hours.
        
        Returns:
            True if in business hours
        """
        tz_str = self.polling_config.get('timezone', 'America/Sao_Paulo')
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        
        business_hours = self.polling_config.get('business_hours', {})
        start_time = business_hours.get('start', '07:01')
        end_time = business_hours.get('end', '18:59')
        
        # Parse times
        current_time = now.time()
        start = datetime.strptime(start_time, '%H:%M').time()
        end = datetime.strptime(end_time, '%H:%M').time()
        
        return start <= current_time <= end
    
    def get_poll_interval(self) -> int:
        """
        Get appropriate poll interval based on time of day.
        
        Returns:
            Interval in seconds
        """
        if self.is_business_hours():
            minutes = self.polling_config.get('business_hours', {}).get('interval_minutes', 6)
        else:
            minutes = self.polling_config.get('off_hours', {}).get('interval_minutes', 2)
        
        return minutes * 60
    
    def cleanup(self):
        """Cleanup resources."""
        self.api_client.close()
        self.logger.info("Poller cleanup complete")
