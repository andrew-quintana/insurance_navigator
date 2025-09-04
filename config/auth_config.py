"""
Authentication configuration for the insurance navigator application.

This module provides configuration settings for authentication features,
including email confirmation toggles for development vs production.
"""

import os
from typing import Dict, Any

class AuthConfig:
    """Authentication configuration settings."""
    
    def __init__(self):
        # Email confirmation settings
        self.email_confirmation_enabled = os.getenv('EMAIL_CONFIRMATION_ENABLED', 'false').lower() == 'true'
        self.auto_confirm_emails = os.getenv('AUTO_CONFIRM_EMAILS', 'true').lower() == 'true'
        
        # Development mode settings
        self.development_mode = os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true'
        self.allow_test_emails = os.getenv('ALLOW_TEST_EMAILS', 'true').lower() == 'true'
        
        # Email validation settings
        self.strict_email_validation = os.getenv('STRICT_EMAIL_VALIDATION', 'false').lower() == 'true'
        
    def get_auth_settings(self) -> Dict[str, Any]:
        """Get authentication settings for Supabase client."""
        settings = {
            'email_confirm': self.auto_confirm_emails,
            'email_confirm_enabled': self.email_confirmation_enabled
        }
        
        # In development mode, auto-confirm all emails
        if self.development_mode:
            settings['email_confirm'] = True
            settings['email_confirm_enabled'] = False
            
        return settings
    
    def is_test_email_allowed(self, email: str) -> bool:
        """Check if test email addresses are allowed."""
        if not self.allow_test_emails:
            return not any(domain in email.lower() for domain in ['@example.com', '@test.com', '@localhost'])
        return True

# Global auth config instance
auth_config = AuthConfig()
