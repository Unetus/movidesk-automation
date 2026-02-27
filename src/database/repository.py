"""Database repository for all data operations."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from contextlib import contextmanager

from .models import Report, ReportTicket, AISummary
from ..utils.logger import get_logger


class DatabaseRepository:
    """
    Handle all database operations.
    
    Features:
    - Connection pooling via context manager
    - Automatic schema initialization
    - AI summary caching (token savings!)
    - Historical data analytics
    """
    
    def __init__(self, db_path: str = "./data/automation.db"):
        """
        Initialize repository.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema if not exists."""
        try:
            with self._get_connection() as conn:
                from .migrations import get_schema
                conn.executescript(get_schema())
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    # ==========================================
    # AI SUMMARY OPERATIONS (CACHE) - TOKEN SAVINGS!
    # ==========================================
    
    def get_ai_summary(self, ticket_id: int) -> Optional[AISummary]:
        """
        Get cached AI summary for a ticket.
        
        Returns None if not cached or too old (>7 days).
        Updates usage statistics automatically.
        
        Args:
            ticket_id: Movidesk ticket ID
        
        Returns:
            Cached AISummary or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM ai_summaries
                    WHERE ticket_id = ?
                    AND generated_at >= datetime('now', '-7 days')
                """, (ticket_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Update usage stats
                conn.execute("""
                    UPDATE ai_summaries
                    SET last_used_at = ?, use_count = use_count + 1
                    WHERE ticket_id = ?
                """, (datetime.now(), ticket_id))
                
                return AISummary(**dict(row))
        
        except Exception as e:
            self.logger.error(f"Error getting AI summary for ticket {ticket_id}: {e}")
            return None
    
    def save_ai_summary(self, summary: AISummary) -> int:
        """
        Save or update AI summary cache.
        
        Args:
            summary: AISummary object to save
        
        Returns:
            Summary ID
        """
        try:
            with self._get_connection() as conn:
                # Check if summary exists
                cursor = conn.execute("""
                    SELECT id, use_count FROM ai_summaries WHERE ticket_id = ?
                """, (summary.ticket_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    conn.execute("""
                        UPDATE ai_summaries
                        SET summary = ?, model_used = ?, tokens_used = ?,
                            generated_at = ?, last_used_at = ?
                        WHERE ticket_id = ?
                    """, (
                        summary.summary,
                        summary.model_used,
                        summary.tokens_used,
                        summary.generated_at or datetime.now(),
                        datetime.now(),
                        summary.ticket_id
                    ))
                    return existing['id']
                else:
                    # Insert new
                    cursor = conn.execute("""
                        INSERT INTO ai_summaries
                        (ticket_id, ticket_number, subject, summary, model_used, 
                         tokens_used, generated_at, last_used_at, use_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        summary.ticket_id,
                        summary.ticket_number,
                        summary.subject,
                        summary.summary,
                        summary.model_used,
                        summary.tokens_used,
                        summary.generated_at or datetime.now(),
                        datetime.now(),
                        0
                    ))
                    return cursor.lastrowid
        
        except Exception as e:
            self.logger.error(f"Error saving AI summary: {e}")
            raise
    
    def get_summary_stats(self) -> Dict:
        """
        Get statistics about cached summaries.
        
        Returns:
            Dictionary with stats: total, tokens used, reuses, etc.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_summaries,
                        COALESCE(SUM(tokens_used), 0) as total_tokens_used,
                        COALESCE(SUM(use_count), 0) as total_reuses,
                        COALESCE(AVG(use_count), 0) as avg_reuses_per_summary
                    FROM ai_summaries
                """)
                
                row = cursor.fetchone()
                if not row:
                    return {
                        'total_summaries': 0,
                        'total_tokens_used': 0,
                        'total_reuses': 0,
                        'avg_reuses_per_summary': 0
                    }
                
                return dict(row)
        
        except Exception as e:
            self.logger.error(f"Error getting summary stats: {e}")
            return {}
    
    def clean_old_summaries(self, days: int = 30) -> int:
        """
        Delete old cached summaries.
        
        Args:
            days: Delete summaries older than this many days
        
        Returns:
            Number of summaries deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM ai_summaries
                    WHERE generated_at < datetime('now', ? || ' days')
                """, (f'-{days}',))
                
                deleted = cursor.rowcount
                if deleted > 0:
                    self.logger.info(f"Cleaned {deleted} old AI summaries (>{days} days)")
                
                return deleted
        
        except Exception as e:
            self.logger.error(f"Error cleaning old summaries: {e}")
            return 0
    
    # ==========================================
    # REPORT OPERATIONS
    # ==========================================
    
    def create_report(self, report: Report) -> int:
        """
        Create new report record.
        
        Args:
            report: Report object to save
        
        Returns:
            Report ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO reports
                    (generated_at, agent_email, total_new, total_overdue, 
                     total_expiring, total_summarized, email_sent, email_subject, 
                     execution_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.generated_at or datetime.now(),
                    report.agent_email,
                    report.total_new,
                    report.total_overdue,
                    report.total_expiring,
                    report.total_summarized,
                    report.email_sent,
                    report.email_subject,
                    report.execution_time_seconds
                ))
                
                report_id = cursor.lastrowid
                self.logger.info(f"Created report with ID {report_id}")
                return report_id
        
        except Exception as e:
            self.logger.error(f"Error creating report: {e}")
            raise
    
    def update_report(
        self, 
        report_id: int, 
        email_sent: bool = None,
        execution_time: float = None
    ) -> bool:
        """
        Update report fields.
        
        Args:
            report_id: Report ID to update
            email_sent: Mark as sent or not
            execution_time: Execution time in seconds
        
        Returns:
            True if updated successfully
        """
        try:
            updates = []
            params = []
            
            if email_sent is not None:
                updates.append("email_sent = ?")
                params.append(email_sent)
            
            if execution_time is not None:
                updates.append("execution_time_seconds = ?")
                params.append(execution_time)
            
            if not updates:
                return True
            
            params.append(report_id)
            
            with self._get_connection() as conn:
                conn.execute(f"""
                    UPDATE reports
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Error updating report {report_id}: {e}")
            return False
    
    def add_ticket_to_report(self, ticket: ReportTicket) -> int:
        """
        Add ticket snapshot to report.
        
        Args:
            ticket: ReportTicket object to save
        
        Returns:
            Ticket record ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO report_tickets
                    (report_id, ticket_id, ticket_number, subject, client_name,
                     status, base_status, urgency, category, created_date,
                     last_update, sla_solution_date, is_overdue, days_overdue,
                     section, movidesk_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket.report_id,
                    ticket.ticket_id,
                    ticket.ticket_number,
                    ticket.subject,
                    ticket.client_name,
                    ticket.status,
                    ticket.base_status,
                    ticket.urgency,
                    ticket.category,
                    ticket.created_date,
                    ticket.last_update,
                    ticket.sla_solution_date,
                    ticket.is_overdue,
                    ticket.days_overdue,
                    ticket.section,
                    ticket.movidesk_url
                ))
                
                return cursor.lastrowid
        
        except Exception as e:
            self.logger.error(f"Error adding ticket to report: {e}")
            raise
    
    def get_report(self, report_id: int, include_tickets: bool = True) -> Optional[Report]:
        """
        Get report by ID with optional tickets.
        
        Args:
            report_id: Report ID
            include_tickets: Load associated tickets
        
        Returns:
            Report object or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                report = Report(**dict(row))
                
                if include_tickets:
                    cursor = conn.execute("""
                        SELECT * FROM report_tickets WHERE report_id = ?
                    """, (report_id,))
                    report.tickets = [ReportTicket(**dict(r)) for r in cursor.fetchall()]
                
                return report
        
        except Exception as e:
            self.logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def get_latest_report(self, agent_email: str = None) -> Optional[Report]:
        """
        Get most recent report.
        
        Args:
            agent_email: Filter by agent email (optional)
        
        Returns:
            Latest Report or None
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM reports"
                params = []
                
                if agent_email:
                    query += " WHERE agent_email = ?"
                    params.append(agent_email)
                
                query += " ORDER BY generated_at DESC LIMIT 1"
                
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                
                return Report(**dict(row)) if row else None
        
        except Exception as e:
            self.logger.error(f"Error getting latest report: {e}")
            return None
    
    def get_reports_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        agent_email: str = None
    ) -> List[Report]:
        """
        Get reports within date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            agent_email: Filter by agent (optional)
        
        Returns:
            List of Report objects
        """
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM reports
                    WHERE generated_at >= ? AND generated_at <= ?
                """
                params = [start_date, end_date]
                
                if agent_email:
                    query += " AND agent_email = ?"
                    params.append(agent_email)
                
                query += " ORDER BY generated_at DESC"
                
                cursor = conn.execute(query, params)
                return [Report(**dict(row)) for row in cursor.fetchall()]
        
        except Exception as e:
            self.logger.error(f"Error getting reports by date range: {e}")
            return []
    
    # ==========================================
    # ANALYTICS
    # ==========================================
    
    def get_comparison_with_yesterday(self, agent_email: str) -> Dict:
        """
        Compare today's stats with yesterday.
        
        Args:
            agent_email: Agent email to filter
        
        Returns:
            Dictionary with today, yesterday, and diff stats
        """
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        DATE(generated_at) as report_date,
                        SUM(total_new) as new_tickets,
                        SUM(total_overdue) as overdue_tickets,
                        SUM(total_expiring) as expiring_tickets
                    FROM reports
                    WHERE agent_email = ?
                    AND DATE(generated_at) IN (?, ?)
                    GROUP BY DATE(generated_at)
                """, (agent_email, str(today), str(yesterday)))
                
                results = {}
                for row in cursor.fetchall():
                    results[str(row['report_date'])] = {
                        'new_tickets': row['new_tickets'] or 0,
                        'overdue_tickets': row['overdue_tickets'] or 0,
                        'expiring_tickets': row['expiring_tickets'] or 0
                    }
                
                today_data = results.get(str(today), {
                    'new_tickets': 0, 
                    'overdue_tickets': 0, 
                    'expiring_tickets': 0
                })
                yesterday_data = results.get(str(yesterday), {
                    'new_tickets': 0, 
                    'overdue_tickets': 0, 
                    'expiring_tickets': 0
                })
                
                return {
                    'today': today_data,
                    'yesterday': yesterday_data,
                    'diff_new': today_data['new_tickets'] - yesterday_data['new_tickets'],
                    'diff_overdue': today_data['overdue_tickets'] - yesterday_data['overdue_tickets'],
                    'diff_expiring': today_data['expiring_tickets'] - yesterday_data['expiring_tickets']
                }
        
        except Exception as e:
            self.logger.error(f"Error getting comparison with yesterday: {e}")
            return {
                'today': {},
                'yesterday': {},
                'diff_new': 0,
                'diff_overdue': 0,
                'diff_expiring': 0
            }
    
    def get_trends(self, agent_email: str, days: int = 30) -> List[Dict]:
        """
        Get trend data for last N days.
        
        Args:
            agent_email: Agent email to filter
            days: Number of days to look back
        
        Returns:
            List of dictionaries with date and stats
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        DATE(generated_at) as date,
                        SUM(total_new) as new_tickets,
                        SUM(total_overdue) as overdue_tickets,
                        SUM(total_expiring) as expiring_tickets
                    FROM reports
                    WHERE agent_email = ? AND generated_at >= ?
                    GROUP BY DATE(generated_at)
                    ORDER BY date ASC
                """, (agent_email, cutoff))
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            self.logger.error(f"Error getting trends: {e}")
            return []
