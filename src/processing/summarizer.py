"""AI-powered ticket summarization using Groq."""

from groq import Groq
from typing import Optional, Dict
import time

from ..api.models import Ticket
from ..config import get_settings, get_config
from ..utils.logger import get_logger
from .html_parser import HTMLParser


class SummarizerError(Exception):
    """Summarization error."""
    pass


class TicketSummarizer:
    """
    Generate AI-powered summaries of tickets using Groq.
    
    Features:
    - Caching to avoid re-summarizing
    - Retry logic for API failures
    - Token management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize summarizer.
        
        Args:
            api_key: Groq API key (from settings if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.config = get_config()
        self.logger = get_logger()
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        # Cache for summaries (ticket_id -> summary)
        self._cache: Dict[str, str] = {}
        
        # Get config
        self.summarization_config = self.config.summarization
    
    def summarize_ticket(self, ticket: Ticket, force: bool = False) -> Optional[str]:
        """
        Generate summary for a ticket.
        
        Args:
            ticket: Ticket to summarize
            force: Force re-summarization even if cached
        
        Returns:
            Summary text or None on error
        """
        # Check if summarization is enabled
        if not self.summarization_config.get('enabled', True):
            self.logger.debug("Summarization is disabled")
            return None
        
        # Check cache
        if not force and ticket.id in self._cache:
            self.logger.debug(f"Using cached summary for ticket {ticket.id}")
            return self._cache[ticket.id]
        
        try:
            # Prepare ticket content
            content = self._prepare_content(ticket)
            
            if not content or len(content.strip()) < 50:
                self.logger.warning(f"Insufficient content for ticket {ticket.id}")
                return None
            
            # Build prompt
            prompt_template = self.summarization_config.get(
                'prompt_template',
                'Resuma este ticket de suporte em 2-3 frases:\n\n{ticket_content}'
            )
            prompt = prompt_template.replace('{ticket_content}', content)
            
            # Call Groq API
            self.logger.debug(f"Generating summary for ticket {ticket.id}")
            summary = self._call_groq(prompt)
            
            # Cache result
            if summary:
                self._cache[ticket.id] = summary
                self.logger.info(f"Generated summary for ticket {ticket.id}")
            
            return summary
        
        except Exception as e:
            self.logger.error(f"Error summarizing ticket {ticket.id}: {e}")
            return None
    
    def _prepare_content(self, ticket: Ticket) -> str:
        """
        Prepare ticket content for summarization.
        
        Args:
            ticket: Ticket object
        
        Returns:
            Formatted content string
        """
        parser = HTMLParser()
        parts = []
        
        # Subject
        if ticket.subject:
            parts.append(f"ASSUNTO: {ticket.subject}")
        
        # Cliente/Unidade (destaque especial)
        if ticket.clients and len(ticket.clients) > 0:
            client = ticket.clients[0]
            client_info = client.businessName or client.email or "Cliente não identificado"
            parts.append(f"\n🏢 CLIENTE/UNIDADE: {client_info}")
        
        # Metadata expandida
        metadata = []
        if ticket.category:
            metadata.append(f"Categoria: {ticket.category}")
        if ticket.urgency:
            metadata.append(f"Urgência: {ticket.urgency}")
        if ticket.status:
            metadata.append(f"Status: {ticket.status}")
        if ticket.owner_name:
            metadata.append(f"Responsável: {ticket.owner_name}")
        
        if metadata:
            parts.append(" | ".join(metadata))
        
        # Informações adicionais
        if ticket.createdDate:
            parts.append(f"\nCriado em: {ticket.createdDate.strftime('%d/%m/%Y %H:%M')}")
        
        if ticket.actionCount:
            parts.append(f"Total de ações/interações: {ticket.actionCount}")
        
        # Latest actions (aumentar para 5 ações)
        latest_actions = ticket.get_latest_actions(5)
        if latest_actions:
            parts.append("\n\n📝 HISTÓRICO DE INTERAÇÕES:")
            for i, action in enumerate(latest_actions, 1):
                # Extract text from HTML if needed
                if action.htmlDescription:
                    text = parser.extract_text(action.htmlDescription)
                else:
                    text = action.description or ""
                
                # Autor da ação
                author = ""
                if action.createdBy:
                    author = f" [{action.createdBy.display_name}]"
                
                # Data da ação
                date_str = ""
                if action.createdDate:
                    date_str = f" em {action.createdDate.strftime('%d/%m %H:%M')}"
                
                # Truncate action text (aumentar limite)
                if len(text) > 600:
                    text = text[:600] + "..."
                
                if text:
                    parts.append(f"\n{i}.{author}{date_str}:\n   {text}")
        
        # Join all parts
        content = "\n".join(parts)
        
        # Truncate to reasonable length (aumentar limite)
        max_chars = 3500  # Aumentado de 3000 para 3500
        if len(content) > max_chars:
            content = content[:max_chars] + "\n[...conteúdo truncado...]"
        
        return content
    
    def _call_groq(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Call Groq API with retry logic.
        
        Args:
            prompt: Prompt text
            max_retries: Maximum retry attempts
        
        Returns:
            Generated summary or None
        """
        model = self.summarization_config.get('model', 'llama-3.1-8b-instant')
        max_tokens = self.summarization_config.get('max_tokens', 150)
        temperature = self.summarization_config.get('temperature', 0.3)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um assistente especializado em resumir tickets de suporte técnico de forma concisa e objetiva."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9
                )
                
                summary = response.choices[0].message.content.strip()
                return summary
            
            except Exception as e:
                error_str = str(e)
                
                # Não fazer retry em erros de configuração (400, modelo inválido, etc.)
                is_config_error = (
                    'Error code: 400' in error_str or 
                    'model_decommissioned' in error_str or
                    'invalid_request_error' in error_str or
                    'model' in error_str.lower() and 'not' in error_str.lower()
                )
                
                if is_config_error:
                    self.logger.error(
                        f"Groq API configuration error: {e}. "
                        f"Check model name in config.yaml. Current: {model}"
                    )
                    raise SummarizerError(f"Configuration error: {e}")
                
                self.logger.warning(
                    f"Groq API error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise SummarizerError(f"Failed after {max_retries} attempts: {e}")
        
        return None
    
    def clear_cache(self):
        """Clear summary cache."""
        self._cache.clear()
        self.logger.debug("Summary cache cleared")
    
    def get_cache_size(self) -> int:
        """Get number of cached summaries."""
        return len(self._cache)
