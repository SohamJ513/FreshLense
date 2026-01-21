# backend/app/services/mfa_service.py
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MFAService:
    """Service for handling Multi-Factor Authentication operations"""
    
    # Configuration
    CODE_LENGTH = 6
    CODE_EXPIRY_MINUTES = 10
    MAX_RESEND_ATTEMPTS = 3
    RESEND_COOLDOWN_MINUTES = 1
    
    @staticmethod
    def generate_mfa_code(length: int = CODE_LENGTH) -> str:
        """
        Generate a random numeric MFA code.
        
        Args:
            length: Length of the code (default: 6)
            
        Returns:
            str: Generated numeric code
        """
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def get_code_expiry(minutes: int = CODE_EXPIRY_MINUTES) -> datetime:
        """
        Calculate expiry time for MFA code.
        
        Args:
            minutes: Minutes until code expires
            
        Returns:
            datetime: Expiry timestamp
        """
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    @staticmethod
    def is_code_expired(expires_at: datetime) -> bool:
        """
        Check if MFA code has expired.
        
        Args:
            expires_at: Code expiry timestamp
            
        Returns:
            bool: True if expired, False otherwise
        """
        return datetime.utcnow() >= expires_at
    
    @staticmethod
    def is_code_valid(
        stored_code: Optional[str], 
        input_code: str, 
        expires_at: Optional[datetime]
    ) -> Tuple[bool, str]:
        """
        Validate MFA code with comprehensive error messages.
        
        Args:
            stored_code: Code stored in database
            input_code: Code provided by user
            expires_at: Code expiry timestamp
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check if code exists
        if not stored_code:
            return False, "No MFA code found. Please request a new code."
        
        # Check if code expired
        if expires_at and MFAService.is_code_expired(expires_at):
            return False, "MFA code has expired. Please request a new code."
        
        # Check if codes match
        if stored_code != input_code:
            return False, "Invalid MFA code. Please try again."
        
        return True, "Code is valid"
    
    @staticmethod
    def can_resend_code(
        last_sent_at: Optional[datetime],
        attempt_count: int = 0
    ) -> Tuple[bool, str]:
        """
        Check if user can request a new MFA code.
        
        Args:
            last_sent_at: When the last code was sent
            attempt_count: Number of resend attempts
            
        Returns:
            Tuple[bool, str]: (can_resend, error_message)
        """
        # Check max attempts
        if attempt_count >= MFAService.MAX_RESEND_ATTEMPTS:
            return False, "Too many resend attempts. Please wait before trying again."
        
        # Check cooldown
        if last_sent_at:
            cooldown_expiry = last_sent_at + timedelta(minutes=MFAService.RESEND_COOLDOWN_MINUTES)
            if datetime.utcnow() < cooldown_expiry:
                time_left = (cooldown_expiry - datetime.utcnow()).seconds
                return False, f"Please wait {time_left} seconds before requesting a new code."
        
        return True, "Can resend code"
    
    @staticmethod
    def format_code_for_email(code: str) -> str:
        """
        Format MFA code for email display (adds spaces for readability).
        
        Args:
            code: The 6-digit code
            
        Returns:
            str: Formatted code (e.g., "123 456")
        """
        if len(code) != 6:
            return code
        
        return f"{code[:3]} {code[3:]}"
    
    @staticmethod
    def generate_mfa_email_content(
        code: str, 
        user_email: str,
        expiry_minutes: int = CODE_EXPIRY_MINUTES
    ) -> dict:
        """
        Generate email content for MFA code.
        
        Args:
            code: The MFA code
            user_email: User's email address
            expiry_minutes: Code expiry time in minutes
            
        Returns:
            dict: Email subject and HTML content
        """
        formatted_code = MFAService.format_code_for_email(code)
        
        subject = f"Your MFA Verification Code: {formatted_code}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .code {{ 
                    font-size: 32px; 
                    font-weight: bold; 
                    letter-spacing: 5px; 
                    text-align: center; 
                    margin: 30px 0;
                    color: #4f46e5;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
                .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FreshLense MFA Verification</h1>
                </div>
                
                <p>Hello,</p>
                
                <p>You've requested to log in to your FreshLense account. Use the verification code below to complete your login:</p>
                
                <div class="code">{formatted_code}</div>
                
                <div class="warning">
                    <p><strong>⚠️ Important:</strong> This code will expire in {expiry_minutes} minutes.</p>
                    <p>If you didn't request this code, please ignore this email or contact support.</p>
                </div>
                
                <p>For security reasons, please do not share this code with anyone.</p>
                
                <p>Thank you,<br>The FreshLense Team</p>
                
                <div class="footer">
                    <p>This email was sent to {user_email}.</p>
                    <p>© {datetime.utcnow().year} FreshLense. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text_content = f"""
        FreshLense MFA Verification
        
        Hello,
        
        You've requested to log in to your FreshLense account. Use the verification code below to complete your login:
        
        Verification Code: {formatted_code}
        
        ⚠️ Important: This code will expire in {expiry_minutes} minutes.
        If you didn't request this code, please ignore this email or contact support.
        
        For security reasons, please do not share this code with anyone.
        
        Thank you,
        The FreshLense Team
        
        This email was sent to {user_email}.
        © {datetime.utcnow().year} FreshLense. All rights reserved.
        """
        
        return {
            "subject": subject,
            "html": html_content,
            "text": plain_text_content
        }
    
    @staticmethod
    def generate_setup_email_content(user_email: str) -> dict:
        """
        Generate email content for MFA setup confirmation.
        
        Args:
            user_email: User's email address
            
        Returns:
            dict: Email subject and HTML content
        """
        subject = "MFA Has Been Enabled on Your FreshLense Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MFA Setup Complete</h1>
                </div>
                
                <p>Hello,</p>
                
                <p>Multi-Factor Authentication (MFA) has been successfully enabled on your FreshLense account.</p>
                
                <p><strong>What this means:</strong></p>
                <ul>
                    <li>Enhanced security for your account</li>
                    <li>You'll receive a verification code via email each time you log in</li>
                    <li>Your account is now better protected against unauthorized access</li>
                </ul>
                
                <p>If you did not enable MFA or believe this was done in error, please contact our support team immediately.</p>
                
                <p>Thank you for helping us keep your account secure!</p>
                
                <p>Best regards,<br>The FreshLense Security Team</p>
                
                <div class="footer">
                    <p>This email was sent to {user_email}.</p>
                    <p>© {datetime.utcnow().year} FreshLense. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            "subject": subject,
            "html": html_content
        }

# Singleton instance
mfa_service = MFAService()