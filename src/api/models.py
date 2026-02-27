"""Pydantic models for Movidesk API responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from datetime import datetime
import pytz


class Person(BaseModel):
    """Person model (client, agent, etc.)."""
    id: Optional[str] = None
    personType: Optional[int] = None
    profileType: Optional[int] = None
    businessName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.businessName or self.email or "Unknown"


class Action(BaseModel):
    """Ticket action model."""
    id: Optional[Union[str, int]] = None
    type: Optional[int] = None
    origin: Optional[int] = None
    description: Optional[str] = None
    htmlDescription: Optional[str] = None
    status: Optional[Union[str, int]] = None
    justification: Optional[str] = None
    createdBy: Optional[Person] = None
    createdDate: Optional[datetime] = None
    isDeleted: Optional[bool] = False
    
    @property
    def text_content(self) -> str:
        """Get text content from action."""
        return self.description or ""


class CustomFieldItem(BaseModel):
    """Custom field item."""
    customFieldId: Optional[str] = None
    customFieldRuleId: Optional[str] = None
    line: Optional[int] = None
    value: Optional[str] = None
    items: Optional[List[Any]] = None


class Ticket(BaseModel):
    """Movidesk ticket model."""
    id: Optional[Union[str, int]] = None
    protocol: Optional[int] = None
    type: Optional[int] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    baseStatus: Optional[str] = None
    justification: Optional[str] = None
    origin: Optional[int] = None
    createdDate: Optional[datetime] = None
    originEmailAccount: Optional[str] = None
    owner: Optional[Person] = None
    ownerTeam: Optional[str] = None
    createdBy: Optional[Person] = None
    serviceFull: Optional[List[Any]] = None
    serviceFirstLevelId: Optional[str] = None
    serviceFirstLevel: Optional[str] = None
    serviceSecondLevel: Optional[str] = None
    serviceThirdLevel: Optional[str] = None
    contactForm: Optional[str] = None
    tags: Optional[List[str]] = None
    cc: Optional[str] = None
    resolvedIn: Optional[datetime] = None
    reopenedIn: Optional[datetime] = None
    closedIn: Optional[datetime] = None
    lastActionDate: Optional[datetime] = None
    actionCount: Optional[int] = None
    lastUpdate: Optional[datetime] = None
    slaDueDate: Optional[datetime] = None  # Data de vencimento do SLA
    slaAgreement: Optional[str] = None  # Nome do acordo SLA
    slaSolutionTime: Optional[int] = None  # Tempo de solução em minutos
    slaSolutionDate: Optional[datetime] = None  # Data de solução do SLA
    dueDate: Optional[datetime] = None  # Data de vencimento
    lifetimeWorkingTime: Optional[int] = None
    stoppedTime: Optional[int] = None
    stoppedTimeWorkingTime: Optional[int] = None
    resolvedInFirstCall: Optional[bool] = None
    chatWidget: Optional[str] = None
    chatGroup: Optional[str] = None
    chatTalkTime: Optional[int] = None
    chatWaitingTime: Optional[int] = None
    clients: Optional[List[Person]] = None
    actions: Optional[List[Action]] = None
    customFieldValues: Optional[List[CustomFieldItem]] = None
    
    @property
    def client_name(self) -> str:
        """Get client name."""
        if self.clients and len(self.clients) > 0:
            return self.clients[0].display_name
        return "No client"
    
    @property
    def owner_name(self) -> str:
        """Get owner name."""
        if self.owner:
            return self.owner.display_name
        return "Unassigned"
    
    @property
    def ticket_number(self) -> str:
        """Get ticket number for display."""
        # Protocol é o número do ticket visível
        if self.protocol:
            return str(self.protocol)
        # Fallback para id se protocol não existir
        if self.id:
            return str(self.id)
        return "N/A"
    
    @property
    def movidesk_url(self) -> str:
        """Get Movidesk ticket URL."""
        # Usar id primeiro (identificador interno), depois protocol
        ticket_id = self.id or self.protocol
        if ticket_id:
            return f"https://atendimento.wifire.me/Ticket/Edit/{ticket_id}"
        return ""
    
    @property
    def resolution_date(self) -> Optional[datetime]:
        """Get resolution date from serviceFull[0].resolutionDate."""
        if not self.serviceFull or not isinstance(self.serviceFull, list) or len(self.serviceFull) == 0:
            return None
        
        service = self.serviceFull[0]
        if isinstance(service, dict) and 'resolutionDate' in service:
            resolution_str = service['resolutionDate']
            if resolution_str:
                try:
                    # Parse ISO format datetime
                    return datetime.fromisoformat(resolution_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        # Try parsing without timezone
                        return datetime.fromisoformat(resolution_str)
                    except (ValueError, AttributeError):
                        return None
        return None
    
    @property
    def is_overdue(self) -> bool:
        """Check if ticket is overdue based on resolution date from serviceFull."""
        # Ticket não pode estar vencido se já está resolvido/fechado
        if self.baseStatus in ['Closed', 'Resolved']:
            return False
        
        # Prioridade: slaSolutionDate > serviceFull[0].resolutionDate > outros campos
        due_date = self.slaSolutionDate or self.resolution_date or self.slaDueDate or self.dueDate
        
        if due_date:
            # IMPORTANTE: Movidesk armazena datas em UTC na API (sem timezone marker)
            # Precisamos converter para UTC para comparação correta
            
            # Converter due_date para UTC se não tiver timezone
            if due_date.tzinfo is None:
                # Assumir que é UTC (padrão do Movidesk)
                utc_tz = pytz.UTC
                due_date_utc = utc_tz.localize(due_date)
            else:
                due_date_utc = due_date.astimezone(pytz.UTC)
            
            # Obter hora atual em UTC
            now_utc = datetime.now(pytz.UTC)
            
            return now_utc > due_date_utc
        
        # Sem SLA definido = não está vencido
        return False
    
    @property
    def effective_due_date(self) -> Optional[datetime]:
        """Get the effective due date (prioritizing slaSolutionDate - campo real da API)."""
        return self.slaSolutionDate or self.resolution_date or self.slaDueDate or self.dueDate
    
    @property
    def days_overdue(self) -> int:
        """Get number of days overdue (0 if not overdue)."""
        if not self.is_overdue:
            return 0
        
        # Calcular dias desde o vencimento do SLA (usando UTC)
        due_date = self.effective_due_date
        if due_date:
            # Converter due_date para UTC
            if due_date.tzinfo is None:
                # Assumir que é UTC (padrão do Movidesk)
                utc_tz = pytz.UTC
                due_date_utc = utc_tz.localize(due_date)
            else:
                due_date_utc = due_date.astimezone(pytz.UTC)
            
            # Obter hora atual em UTC
            now_utc = datetime.now(pytz.UTC)
            
            delta = now_utc - due_date_utc
            return max(0, delta.days)
        
        return 0
    
    def get_latest_actions(self, limit: int = 5) -> List[Action]:
        """Get latest N actions."""
        if not self.actions:
            return []
        
        # Sort by created date descending
        sorted_actions = sorted(
            [a for a in self.actions if not a.isDeleted],
            key=lambda x: x.createdDate or datetime.min,
            reverse=True
        )
        return sorted_actions[:limit]
    
    def get_text_content(self) -> str:
        """Get combined text content for summarization."""
        parts = []
        
        # Add subject
        if self.subject:
            parts.append(f"Assunto: {self.subject}")
        
        # Add category and urgency
        if self.category:
            parts.append(f"Categoria: {self.category}")
        if self.urgency:
            parts.append(f"Urgência: {self.urgency}")
        
        # Add latest actions
        latest_actions = self.get_latest_actions(3)
        if latest_actions:
            parts.append("\nÚltimas ações:")
            for action in latest_actions:
                if action.text_content:
                    parts.append(f"- {action.text_content[:300]}")
        
        return "\n".join(parts)


class TicketListResponse(BaseModel):
    """Response from ticket list endpoint."""
    items: List[Ticket] = Field(default_factory=list)
    total: Optional[int] = None
