from pathlib import Path
from typing import Optional
import email
from email import policy
from bs4 import BeautifulSoup
from loguru import logger

class EMLParser:
    def __init__(self):
        # Create a new policy with no line length limit
        self.policy = policy.default.clone(
            max_line_length=None  # This is the correct way to set no line length limit
        )
    
    def convert_to_html(self, eml_path: Path) -> str:
        """
        Convert an EML file to HTML format.
        
        Args:
            eml_path: Path to the EML file
            
        Returns:
            str: HTML content of the email
        """
        try:
            # Read and parse the EML file
            with open(eml_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=self.policy)
            
            # Get the HTML content
            html_content = self._extract_html_content(msg)
            if not html_content:
                # If no HTML content found, convert text to HTML
                text_content = self._extract_text_content(msg)
                html_content = self._text_to_html(text_content)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error parsing EML file {eml_path}: {str(e)}")
            raise
    
    def _extract_html_content(self, msg: email.message.Message) -> Optional[str]:
        """Extract HTML content from the email message."""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_content()
        return None
    
    def _extract_text_content(self, msg: email.message.Message) -> str:
        """Extract text content from the email message."""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        return ""
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML format."""
        # Create a basic HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Converted Email</title>
        </head>
        <body>
            <pre>{text}</pre>
        </body>
        </html>
        """
        return html 