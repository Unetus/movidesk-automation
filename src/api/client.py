"""Movidesk API client."""

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
from urllib.parse import urlencode

from .models import Ticket
from ..config import get_settings
from ..utils.logger import get_logger
from ..utils.rate_limiter import RateLimiter


class MovideskAPIError(Exception):
    """Movidesk API error."""
    pass


class MovideskClient:
    """
    Movidesk API client with rate limiting and retry logic.
    
    Handles:
    - Rate limiting (10 req/min during business hours)
    - Automatic retries with exponential backoff
    - OData filtering
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        rate_limit: int = 10,
        time_window: int = 60
    ):
        """
        Initialize Movidesk client.
        
        Args:
            api_token: Movidesk API token (from settings if not provided)
            base_url: API base URL (from settings if not provided)
            rate_limit: Max requests per time window
            time_window: Time window in seconds
        """
        settings = get_settings()
        self.api_token = api_token or settings.movidesk_token
        self.base_url = (base_url or settings.movidesk_base_url).rstrip('/')
        self.logger = get_logger()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(rate_limit, time_window)
        
        # HTTP client
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
    
    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL with query parameters."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add token to params
        if params is None:
            params = {}
        params['token'] = self.api_token
        
        # Build query string
        query_string = urlencode(params, safe='$,()\'')
        return f"{url}?{query_string}"
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Make HTTP request with rate limiting and retries.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body
            max_retries: Maximum retry attempts
        
        Returns:
            Response JSON
        
        Raises:
            MovideskAPIError: On API error
        """
        url = self._build_url(endpoint, params)
        retry_count = 0
        backoff = 1.0
        
        while retry_count <= max_retries:
            # Rate limiting
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 0:
                self.logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            
            self.rate_limiter.acquire()
            
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    json=json_data
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(
                        f"Rate limit exceeded. Retrying after {retry_after}s"
                    )
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                
                # Handle other errors
                if response.status_code >= 400:
                    error_msg = f"API error {response.status_code}: {response.text}"
                    self.logger.error(error_msg)
                    
                    if retry_count < max_retries and response.status_code >= 500:
                        # Retry on server errors
                        time.sleep(backoff)
                        backoff *= 2
                        retry_count += 1
                        continue
                    
                    raise MovideskAPIError(error_msg)
                
                # Success
                return response.json()
            
            except httpx.RequestError as e:
                self.logger.error(f"Request error: {e}")
                if retry_count < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    retry_count += 1
                    continue
                raise MovideskAPIError(f"Request failed: {e}")
        
        raise MovideskAPIError(f"Max retries ({max_retries}) exceeded")
    
    def get_tickets(
        self,
        select_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        expand: Optional[List[str]] = None,
        top: int = 100,
        skip: int = 0,
        order_by: Optional[str] = None
    ) -> List[Ticket]:
        """
        Get tickets with OData filtering.
        
        Args:
            select_fields: Fields to select (required for list)
            filter_expr: OData filter expression
            expand: Related entities to expand
            top: Number of records to return
            skip: Number of records to skip
            order_by: Field to order by
        
        Returns:
            List of tickets
        """
        params: Dict[str, Any] = {}
        
        # Required: $select for list queries
        if select_fields:
            params['$select'] = ','.join(select_fields)
        else:
            # Default fields - apenas campos que existem na API
            params['$select'] = ','.join([
                'id', 'protocol', 'subject', 'category', 'urgency', 'status', 'baseStatus',
                'owner', 'clients', 'lastUpdate', 'createdDate', 'actions',
                # Campo de serviço/SLA (resolutionDate está dentro dele)
                'serviceFull',
                # Data de solução do SLA (campo real encontrado via HTML inspection!)
                'slaSolutionDate'
            ])
        
        if filter_expr:
            params['$filter'] = filter_expr
        
        if expand:
            params['$expand'] = ','.join(expand)
        
        if top:
            params['$top'] = top
        
        if skip:
            params['$skip'] = skip
        
        if order_by:
            params['$orderby'] = order_by
        
        self.logger.debug(f"Fetching tickets with params: {params}")
        
        try:
            response = self._request('GET', '/tickets', params=params)
            
            # Response can be a list or a single object
            if isinstance(response, list):
                # Log primeiro ticket para debug
                if response and len(response) > 0:
                    import json
                    self.logger.info("=== RAW API RESPONSE (first ticket) ===")
                    self.logger.info(json.dumps(response[0], indent=2, default=str, ensure_ascii=False))
                    self.logger.info("=== END RAW API RESPONSE ===")
                
                tickets = [Ticket(**ticket_data) for ticket_data in response]
            else:
                tickets = [Ticket(**response)]
            
            self.logger.info(f"Retrieved {len(tickets)} tickets")
            return tickets
        
        except Exception as e:
            self.logger.error(f"Error fetching tickets: {e}")
            raise
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """
        Get single ticket by ID.
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            Ticket or None if not found
        """
        try:
            response = self._request('GET', f'/tickets', params={'id': ticket_id})
            return Ticket(**response)
        except MovideskAPIError:
            return None
    
    def build_filter(
        self,
        last_update_after: Optional[datetime] = None,
        assigned_to_email: Optional[str] = None,
        urgencies: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        exclude_closed: bool = True
    ) -> str:
        """
        Build OData filter expression.
        
        Args:
            last_update_after: Filter tickets updated after this datetime
            assigned_to_email: Filter by assigned agent email
            urgencies: Filter by urgency levels
            statuses: Filter by status
            exclude_closed: Exclude closed tickets
        
        Returns:
            OData filter string
        """
        filters = []
        
        # Last update
        if last_update_after:
            # Format: 2026-02-26T10:00:00.00Z
            dt_str = last_update_after.strftime('%Y-%m-%dT%H:%M:%S.00Z')
            filters.append(f"lastUpdate gt {dt_str}")
        
        # Assigned to
        if assigned_to_email:
            filters.append(f"owner/email eq '{assigned_to_email}'")
        
        # Urgencies
        if urgencies:
            urgency_filters = [f"urgency eq '{u}'" for u in urgencies]
            filters.append(f"({' or '.join(urgency_filters)})")
        
        # Statuses
        if statuses:
            status_filters = [f"status eq '{s}'" for s in statuses]
            filters.append(f"({' or '.join(status_filters)})")
        
        # Exclude closed
        if exclude_closed:
            filters.append("baseStatus ne 'Closed'")
        
        return ' and '.join(filters) if filters else None
    
    def get_latest_tickets_for_agent(
        self,
        agent_email: str,
        limit: int = 5,
        exclude_closed: bool = True
    ) -> List[Ticket]:
        """
        Get latest N tickets for specific agent.
        
        Args:
            agent_email: Agent email address
            limit: Number of tickets to retrieve
            exclude_closed: Exclude closed tickets
        
        Returns:
            List of tickets ordered by urgency and date
        """
        # Build simple filter
        filter_parts = [f"owner/email eq '{agent_email}'"]
        
        if exclude_closed:
            filter_parts.append("baseStatus ne 'Closed'")
        
        filter_expr = ' and '.join(filter_parts)
        
        self.logger.info(f"Fetching latest {limit} tickets for {agent_email}")
        
        # Fetch tickets ordered by lastUpdate descending
        # serviceFull já vem automaticamente, não precisa expand
        tickets = self.get_tickets(
            filter_expr=filter_expr,
            expand=['actions', 'owner', 'clients'],
            order_by='lastUpdate desc',
            top=limit
        )
        
        # Sort by urgency priority (in Python for better control)
        urgency_priority = {
            'Critical': 0,
            'Urgent': 1,
            'High': 2,
            'Medium': 3,
            'Normal': 4,
            'Low': 5,
            None: 6
        }
        
        tickets.sort(key=lambda t: (
            urgency_priority.get(t.urgency, 6),
            -(t.lastUpdate.timestamp() if t.lastUpdate else 0)
        ))
        
        return tickets
    
    def get_overdue_tickets_for_agent(
        self,
        agent_email: str,
        limit: int = 50
    ) -> List[Ticket]:
        """
        Get overdue tickets for specific agent.
        
        Args:
            agent_email: Agent email address
            limit: Maximum number of tickets to retrieve
        
        Returns:
            List of overdue tickets ordered by days overdue (most critical first)
        """
        # Build filter for ALL OPEN tickets (sem filtro de SLA na query)
        filter_parts = [
            f"owner/email eq '{agent_email}'",
            "baseStatus ne 'Closed'",
            "baseStatus ne 'Resolved'"
        ]
        
        filter_expr = ' and '.join(filter_parts)
        
        self.logger.info(f"Fetching all open tickets for {agent_email} to check SLA status")
        
        # Fetch ALL open tickets
        # serviceFull é retornado automaticamente (não precisa expand)
        tickets = self.get_tickets(
            filter_expr=filter_expr,
            expand=['actions', 'owner', 'clients'],
            order_by='lastUpdate desc',
            top=limit
        )
        
        self.logger.info(f"Retrieved {len(tickets)} open tickets. Analyzing SLA status...")
        
        # Debug: verificar TODOS os campos de data dos primeiros tickets
        if tickets:
            self.logger.info("=== DEBUG: Analyzing first 2 tickets ===")
            for i, sample in enumerate(tickets[:2]):
                self.logger.info(f"\n--- Ticket #{sample.ticket_number} ({sample.subject[:40]}) ---")
                self.logger.info(f"  baseStatus: {sample.baseStatus}")
                self.logger.info(f"  status: {sample.status}")
                self.logger.info(f"  urgency: {sample.urgency}")
                self.logger.info(f"  createdDate: {sample.createdDate}")
                self.logger.info(f"  lastUpdate: {sample.lastUpdate}")
                self.logger.info(f"  serviceFull (raw): {sample.serviceFull}")
                self.logger.info(f"  serviceFull type: {type(sample.serviceFull)}")
                if sample.serviceFull:
                    self.logger.info(f"  serviceFull length: {len(sample.serviceFull) if isinstance(sample.serviceFull, list) else 'not a list'}")
                self.logger.info(f"  resolution_date (serviceFull[0].resolutionDate): {sample.resolution_date}")
                self.logger.info(f"  slaDueDate: {sample.slaDueDate}")
                self.logger.info(f"  slaSolutionDate: {sample.slaSolutionDate}")
                self.logger.info(f"  dueDate: {sample.dueDate}")
                self.logger.info(f"  slaAgreement: {sample.slaAgreement}")
                self.logger.info(f"  slaSolutionTime: {sample.slaSolutionTime}")
                self.logger.info(f"  effective_due_date: {sample.effective_due_date}")
                self.logger.info(f"  is_overdue: {sample.is_overdue}")
                self.logger.info(f"  days_overdue: {sample.days_overdue}")
                self.logger.info(f"  Current time: {datetime.now()}")
        
        # Filtrar apenas tickets com vencimento definido
        overdue_tickets = []
        tickets_with_sla = 0
        
        for ticket in tickets:
            # Contar tickets com algum campo de vencimento
            if ticket.effective_due_date:
                tickets_with_sla += 1
                if ticket.is_overdue:
                    overdue_tickets.append(ticket)
                    # Detectar qual campo foi usado
                    if ticket.resolution_date:
                        due_field = "serviceFull[0].resolutionDate"
                    elif ticket.slaDueDate:
                        due_field = "slaDueDate"
                    elif ticket.slaSolutionDate:
                        due_field = "slaSolutionDate"
                    else:
                        due_field = "dueDate"
                    
                    self.logger.info(
                        f"  ⚠️ OVERDUE: Ticket #{ticket.ticket_number} - "
                        f"Due ({due_field}): {ticket.effective_due_date.strftime('%d/%m/%Y %H:%M')} - "
                        f"{ticket.days_overdue} days late"
                    )
        
        self.logger.info(f"\n=== SUMMARY ===")
        self.logger.info(f"Total open tickets: {len(tickets)}")
        self.logger.info(f"Tickets with SLA/due date defined: {tickets_with_sla}/{len(tickets)}")
        
        # Ordenar por dias de atraso (mais atrasado primeiro)
        overdue_tickets.sort(key=lambda t: t.days_overdue, reverse=True)
        
        if overdue_tickets:
            self.logger.info(f"✅ Found {len(overdue_tickets)} ticket(s) with SLA BREACH out of {len(tickets)} open tickets")
            for i, t in enumerate(overdue_tickets[:3]):
                self.logger.info(f"  #{i+1}: Ticket {t.ticket_number} - {t.days_overdue} days overdue - slaDueDate: {t.slaDueDate}")
        else:
            self.logger.info(f"❌ No overdue tickets found among {len(tickets)} open tickets")
            # Log amostras para debug
            if tickets:
                self.logger.info("Sample of tickets checked:")
                for t in tickets[:3]:
                    self.logger.info(f"  Ticket {t.ticket_number}: slaDueDate={t.slaDueDate}, status={t.baseStatus}")
        
        return overdue_tickets
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
