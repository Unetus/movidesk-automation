"""HTML content parser and text extraction."""

from bs4 import BeautifulSoup
from typing import Optional
import re


class HTMLParser:
    """Parse HTML content from ticket descriptions."""
    
    @staticmethod
    def extract_text(html_content: Optional[str]) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html_content: HTML string
        
        Returns:
            Clean text content
        """
        if not html_content:
            return ""
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'meta', 'link']):
                element.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
        
        except Exception:
            # Fallback: simple tag removal
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    @staticmethod
    def clean_description(description: Optional[str], max_length: int = 2000) -> str:
        """
        Clean and truncate description text.
        
        Args:
            description: Raw description text (HTML or plain)
            max_length: Maximum length in characters
        
        Returns:
            Cleaned text
        """
        if not description:
            return ""
        
        # Check if it's HTML
        if '<' in description and '>' in description:
            text = HTMLParser.extract_text(description)
        else:
            text = description
        
        # Truncate if needed
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text
    
    @staticmethod
    def extract_urls(html_content: Optional[str]) -> list[str]:
        """
        Extract URLs from HTML content.
        
        Args:
            html_content: HTML string
        
        Returns:
            List of URLs
        """
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.find_all('a', href=True)
            return [link['href'] for link in links]
        except Exception:
            return []
