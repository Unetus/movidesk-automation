"""Database models (dataclasses for ORM-like operations)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Report:
    """
    Report database model.
    
    Represents a complete daily report generation.
    """
    id: Optional[int] = None
    generated_at: Optional[datetime] = None
    agent_email: Optional[str] = None
    total_new: int = 0
    total_overdue: int = 0
    total_expiring: int = 0
    total_summarized: int = 0
    email_sent: bool = False
    email_subject: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    created_at: Optional[datetime] = None
    
    # Relationships (loaded separately)
    tickets: Optional[List['ReportTicket']] = field(default=None, repr=False)


@dataclass
class ReportTicket:
    """
    Ticket snapshot in a report.
    
    Stores the state of a ticket at the time of report generation.
    """
    id: Optional[int] = None
    report_id: Optional[int] = None
    ticket_id: Optional[int] = None
    ticket_number: Optional[str] = None
    subject: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    base_status: Optional[str] = None
    urgency: Optional[str] = None
    category: Optional[str] = None
    created_date: Optional[datetime] = None
    last_update: Optional[datetime] = None
    sla_solution_date: Optional[datetime] = None
    is_overdue: bool = False
    days_overdue: int = 0
    section: Optional[str] = None  # 'new', 'overdue', 'expiring'
    movidesk_url: Optional[str] = None
    
    # Relationship
    ai_summary: Optional['AISummary'] = field(default=None, repr=False)


@dataclass
class AISummary:
    """
    Cached AI summary for a ticket.
    
    This is the KEY to token savings - summaries are cached and reused!
    """
    id: Optional[int] = None
    ticket_id: Optional[int] = None
    ticket_number: Optional[str] = None
    subject: Optional[str] = None
    summary: Optional[str] = None
    model_used: str = 'llama-3.3-70b-versatile'
    tokens_used: Optional[int] = None
    generated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    created_at: Optional[datetime] = None
