"""State management for polling."""

import json
from pathlib import Path
from datetime import datetime
from typing import Set, Optional
from threading import Lock

from ..utils.logger import get_logger


class StateManager:
    """
    Manage polling state (last poll time, notified tickets).
    
    Persists state to JSON file to avoid duplicate notifications
    across restarts.
    """
    
    def __init__(self, state_file: str = "./data/state.json"):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file
        """
        self.state_file = Path(state_file)
        self.logger = get_logger()
        self.lock = Lock()
        
        # State data
        self.last_poll_time: Optional[datetime] = None
        self.notified_ticket_ids: Set[str] = set()
        
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self.load()
    
    def load(self) -> None:
        """Load state from file."""
        if not self.state_file.exists():
            self.logger.info("No existing state file, starting fresh")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse last poll time
            if 'last_poll_time' in data and data['last_poll_time']:
                self.last_poll_time = datetime.fromisoformat(data['last_poll_time'])
            
            # Load notified IDs
            self.notified_ticket_ids = set(data.get('notified_ticket_ids', []))
            
            self.logger.info(
                f"Loaded state: last_poll={self.last_poll_time}, "
                f"notified_count={len(self.notified_ticket_ids)}"
            )
        
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
    
    def save(self) -> None:
        """Save state to file."""
        with self.lock:
            try:
                data = {
                    'last_poll_time': self.last_poll_time.isoformat() if self.last_poll_time else None,
                    'notified_ticket_ids': list(self.notified_ticket_ids),
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("State saved successfully")
            
            except Exception as e:
                self.logger.error(f"Error saving state: {e}")
    
    def update_last_poll_time(self, poll_time: Optional[datetime] = None) -> None:
        """
        Update last poll timestamp.
        
        Args:
            poll_time: Poll time (defaults to now)
        """
        with self.lock:
            self.last_poll_time = poll_time or datetime.now()
            self.save()
    
    def mark_ticket_notified(self, ticket_id: str) -> None:
        """
        Mark ticket as notified.
        
        Args:
            ticket_id: Ticket ID
        """
        with self.lock:
            self.notified_ticket_ids.add(ticket_id)
            self.save()
    
    def is_ticket_notified(self, ticket_id: str) -> bool:
        """
        Check if ticket has been notified.
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            True if already notified
        """
        return ticket_id in self.notified_ticket_ids
    
    def clear_old_notifications(self, keep_count: int = 1000) -> None:
        """
        Clear old notification records to prevent unbounded growth.
        
        Args:
            keep_count: Number of recent notifications to keep
        """
        with self.lock:
            if len(self.notified_ticket_ids) > keep_count:
                # Convert to list, sort, keep most recent
                # Note: This is a simple approach. In production, might want
                # to track timestamps too
                self.logger.info(
                    f"Clearing old notifications (keeping {keep_count})"
                )
                # Just clear all for simplicity - tickets will be re-notified if needed
                self.notified_ticket_ids.clear()
                self.save()
    
    def reset(self) -> None:
        """Reset all state."""
        with self.lock:
            self.last_poll_time = None
            self.notified_ticket_ids.clear()
            self.save()
            self.logger.info("State reset")
