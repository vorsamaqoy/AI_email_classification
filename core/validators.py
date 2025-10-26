from typing import Dict
import logging
from config.models import ClassifierConfig

logger = logging.getLogger(__name__)

class InputValidator:
    """Validates and preprocesses email input data"""
    
    def __init__(self, config: ClassifierConfig):
        self.config = config
    
    def validate_email_data(self, email_data: Dict) -> Dict:
        """Validate and clean email input data"""
        # Handle missing subject
        if 'subject' not in email_data or not email_data['subject']:
            logger.warning("Missing or empty subject, using default")
            email_data['subject'] = "No Subject"
        
        # Handle missing content
        if 'testo_email' not in email_data or not email_data['testo_email']:
            logger.warning("Empty email content, using subject as content")
            email_data['testo_email'] = email_data.get('subject', 'No content provided')
        
        # Ensure string types
        email_data['subject'] = str(email_data['subject'])
        email_data['testo_email'] = str(email_data['testo_email'])
        
        # Truncate if too long
        email_data = self._truncate_fields(email_data)
        
        return email_data
    
    def _truncate_fields(self, email_data: Dict) -> Dict:
        """Truncate fields to configured maximum lengths"""
        # Truncate email content
        if len(email_data['testo_email']) > self.config.processing.max_email_length:
            original_length = len(email_data['testo_email'])
            email_data['testo_email'] = email_data['testo_email'][:self.config.processing.max_email_length]
            logger.warning(f"Truncated email content: {original_length} -> {self.config.processing.max_email_length}")
        
        # Truncate subject
        if len(email_data['subject']) > self.config.processing.max_subject_length:
            original_length = len(email_data['subject'])
            email_data['subject'] = email_data['subject'][:self.config.processing.max_subject_length]
            logger.warning(f"Truncated subject: {original_length} -> {self.config.processing.max_subject_length}")
        
        return email_data
    
    def prepare_text_for_classification(self, subject: str, content: str, sender: str = "") -> str:
        """Prepare combined text for classification"""
        return f"{subject} {content} {sender}".lower().strip()