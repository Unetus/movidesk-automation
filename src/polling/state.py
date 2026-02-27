"""State management for polling with multi-agent support."""

import json
from pathlib import Path
from datetime import datetime
from typing import Set, Optional, Dict
from threading import Lock

from ..utils.logger import get_logger


class StateManager:
    """
    Manage polling state (last poll time, notified tickets) with multi-agent support.
    
    Persists state to JSON file to avoid duplicate notifications
    across restarts. Supports both single-agent (legacy) and multi-agent modes.
    
    Version 2.0: Multi-agent support with backward compatibility
    """
    
    def __init__(self, state_file: str = "./data/state.json", agent_email: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file
            agent_email: Email of specific agent (for multi-agent mode).
                        If None, uses legacy single-agent mode.
        """
        self.state_file = Path(state_file)
        self.logger = get_logger()
        self.lock = Lock()
        self.agent_email = agent_email
        
        # State data (multi-agent structure)
        # Format: {"agents": {"email@": {"last_poll_time": "...", "notified_ticket_ids": [...]}}}
        self.agents_state: Dict[str, Dict] = {}
        
        # Legacy single-agent state (for backward compatibility)
        self.last_poll_time: Optional[datetime] = None
        self.notified_ticket_ids: Set[str] = set()
        
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self.load()
    
    def load(self) -> None:
        """Load state from file with automatic migration from legacy format."""
        if not self.state_file.exists():
            self.logger.info("No existing state file, starting fresh")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's new multi-agent format
            if 'agents' in data:
                # Load multi-agent state
                self.agents_state = data['agents']
                self.logger.info(
                    f"Loaded multi-agent state: {len(self.agents_state)} agent(s) tracked"
                )
            else:
                # Legacy single-agent format - migrate
                self.logger.info("Migrating legacy single-agent state to multi-agent format...")
                
                # Parse legacy state
                if 'last_poll_time' in data and data['last_poll_time']:
                    self.last_poll_time = datetime.fromisoformat(data['last_poll_time'])
                
                self.notified_ticket_ids = set(data.get('notified_ticket_ids', []))
                
                # If agent_email is provided, migrate to multi-agent format
                if self.agent_email:
                    self.agents_state[self.agent_email] = {
                        'last_poll_time': data.get('last_poll_time'),
                        'notified_ticket_ids': data.get('notified_ticket_ids', [])
                    }
                    self.save()  # Save migrated format
                    self.logger.info(f"Migrated state for agent: {self.agent_email}")
        
        except Exception as e:
            self.logger.error(f"Error loading state: {e}", exc_info=True)
    
    def save(self) -> None:
        """Save state to file in multi-agent format."""
        with self.lock:
            try:
                data = {
                    'agents': self.agents_state,
                    'saved_at': datetime.now().isoformat(),
                    'version': '2.0'  # Mark as multi-agent version
                }
                
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("State saved successfully (multi-agent format)")
            
            except Exception as e:
                self.logger.error(f"Error saving state: {e}")
    
    def _get_agent_state(self, agent_email: Optional[str] = None) -> Dict:
        """
        Get or create state dict for specific agent.
        
        Args:
            agent_email: Agent email (uses self.agent_email if not provided)
        
        Returns:
            Agent state dictionary
        """
        email = agent_email or self.agent_email
        if not email:
            raise ValueError("Agent email must be provided for multi-agent mode")
        
        if email not in self.agents_state:
            self.agents_state[email] = {
                'last_poll_time': None,
                'notified_ticket_ids': []
            }
        
        return self.agents_state[email]
    
    def update_last_poll_time(self, poll_time: Optional[datetime] = None, agent_email: Optional[str] = None) -> None:
        """
        Update last poll timestamp for specific agent.
        
        Args:
            poll_time: Poll time (defaults to now)
            agent_email: Agent email (uses self.agent_email if not provided)
        """
        with self.lock:
            email = agent_email or self.agent_email
            poll_time = poll_time or datetime.now()
            
            if email:
                # Multi-agent mode
                agent_state = self._get_agent_state(email)
                agent_state['last_poll_time'] = poll_time.isoformat()
            else:
                # Legacy single-agent mode
                self.last_poll_time = poll_time
            
            self.save()
    
    def mark_ticket_notified(self, ticket_id: str, agent_email: Optional[str] = None) -> None:
        """
        Mark ticket as notified for specific agent.
        
        Args:
            ticket_id: Ticket ID
            agent_email: Agent email (uses self.agent_email if not provided)
        """
        with self.lock:
            email = agent_email or self.agent_email
            
            if email:
                # Multi-agent mode
                agent_state = self._get_agent_state(email)
                if ticket_id not in agent_state['notified_ticket_ids']:
                    agent_state['notified_ticket_ids'].append(ticket_id)
            else:
                # Legacy single-agent mode
                self.notified_ticket_ids.add(ticket_id)
            
            self.save()
    
    def is_ticket_notified(self, ticket_id: str, agent_email: Optional[str] = None) -> bool:
        """
        Check if ticket has been notified for specific agent.
        
        Args:
            ticket_id: Ticket ID
            agent_email: Agent email (uses self.agent_email if not provided)
        
        Returns:
            True if already notified
        """
        email = agent_email or self.agent_email
        
        if email:
            # Multi-agent mode
            agent_state = self._get_agent_state(email)
            return ticket_id in agent_state['notified_ticket_ids']
        else:
            # Legacy single-agent mode
            return ticket_id in self.notified_ticket_ids
    
    def get_last_poll_time(self, agent_email: Optional[str] = None) -> Optional[datetime]:
        """
        Get last poll time for specific agent.
        
        Args:
            agent_email: Agent email (uses self.agent_email if not provided)
        
        Returns:
            Last poll datetime or None
        """
        email = agent_email or self.agent_email
        
        if email:
            # Multi-agent mode
            agent_state = self._get_agent_state(email)
            poll_time_str = agent_state.get('last_poll_time')
            if poll_time_str:
                return datetime.fromisoformat(poll_time_str)
        else:
            # Legacy single-agent mode
            return self.last_poll_time
        
        return None
    
    def clear_old_notifications(self, keep_count: int = 1000, agent_email: Optional[str] = None) -> None:
        """
        Clear old notification records to prevent unbounded growth.
        
        Args:
            keep_count: Number of recent notifications to keep
            agent_email: Agent email (uses self.agent_email if not provided, None clears all agents)
        """
        with self.lock:
            if agent_email or self.agent_email:
                # Clear for specific agent
                email = agent_email or self.agent_email
                agent_state = self._get_agent_state(email)
                
                if len(agent_state['notified_ticket_ids']) > keep_count:
                    self.logger.info(
                        f"Clearing old notifications for {email} (keeping {keep_count})"
                    )
                    agent_state['notified_ticket_ids'] = agent_state['notified_ticket_ids'][-keep_count:]
                    self.save()
            else:
                # Clear for all agents (legacy)
                if len(self.notified_ticket_ids) > keep_count:
                    self.logger.info(f"Clearing old notifications (keeping {keep_count})")
                    self.notified_ticket_ids.clear()
                    self.save()
    
    def reset(self, agent_email: Optional[str] = None) -> None:
        """
        Reset state for specific agent or all agents.
        
        Args:
            agent_email: Agent email to reset (None resets all)
        """
        with self.lock:
            if agent_email:
                # Reset specific agent
                if agent_email in self.agents_state:
                    del self.agents_state[agent_email]
                    self.logger.info(f"State reset for agent: {agent_email}")
            else:
                # Reset all
                self.last_poll_time = None
                self.notified_ticket_ids.clear()
                self.agents_state.clear()
                self.logger.info("State reset for all agents")
            
            self.save()

