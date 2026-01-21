# backend/app/services/email_service.py
import os
import logging
import resend  # Added Resend import
from typing import Optional
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Resend Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info("✅ Resend initialized with API key")
else:
    logger.warning("⚠️ RESEND_API_KEY not set, emails will only print to console")

async def send_email(to_email: str, subject: str, html: str, text: Optional[str] = None):
    """
    Send email using Resend if configured, otherwise print to console.
    """
    # If Resend is configured, send real email
    if RESEND_API_KEY:
        try:
            params = {
                "from": RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # Add text version if provided
            if text:
                params["text"] = text
                
            response = resend.Emails.send(params)
            logger.info(f"✅ Email sent via Resend to {to_email}, ID: {response['id']}")
            
            # Also print to console for debugging (without full content)
            print("=" * 60)
            print(f"📧 EMAIL SENT VIA RESEND")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Status: Sent via Resend (ID: {response['id']})")
            print("=" * 60)
            
            return {"id": response['id'], "status": "sent", "to": to_email}
            
        except Exception as e:
            logger.error(f"❌ Failed to send email via Resend: {e}")
            # Fallback to console logging
            print_fallback_email(to_email, subject, html, text, "Resend Failed")
            return {"id": "error", "status": "failed", "to": to_email, "error": str(e)}
    else:
        # Development mode - print to console
        print_fallback_email(to_email, subject, html, text, "Console Only")
        return {"id": "simulated", "status": "sent", "to": to_email}

def print_fallback_email(to_email: str, subject: str, html: str, text: Optional[str] = None, mode: str = "Console Only"):
    """Print email to console for development."""
    print("=" * 60)
    print(f"📧 EMAIL ({mode})")
    print("=" * 60)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    if text:
        print(f"Text:\n{text}")
    print(f"HTML preview:\n{html[:200]}...")
    print("=" * 60)

async def send_mfa_email(to_email: str, mfa_code: str, user_email: str):
    """
    Send MFA verification email.
    """
    subject = "Your FreshLense Verification Code"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">FreshLense</h1>
        </div>
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #4f46e5; margin-top: 0;">Your Verification Code</h2>
            <p>Hello {user_email},</p>
            <p>Your verification code for FreshLense is:</p>
            <div style="text-align: center; margin: 30px 0;">
                <div style="display: inline-block; background: #f3f4f6; padding: 20px 40px; border-radius: 8px; border: 2px dashed #4f46e5;">
                    <h1 style="font-size: 32px; letter-spacing: 10px; color: #4f46e5; margin: 0; font-weight: bold;">{mfa_code}</h1>
                </div>
            </div>
            <p style="color: #666; font-size: 14px;">This code will expire in 10 minutes.</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you didn't request this code, please ignore this email.
            </p>
            <p style="margin-top: 30px;">
                Thank you,<br>
                <strong>The FreshLense Team</strong>
            </p>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© {datetime.now().year} FreshLense. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Your FreshLense Verification Code
    
    Hello {user_email},
    
    Your verification code is: {mfa_code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this code, please ignore this email.
    
    Thank you,
    The FreshLense Team
    """
    
    return await send_email(to_email, subject, html, text)

async def send_mfa_setup_email(user_email: str):
    """
    Send MFA setup confirmation email.
    """
    subject = "MFA Enabled Successfully"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">FreshLense Security</h1>
        </div>
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #059669; margin-top: 0;">✅ MFA Enabled Successfully</h2>
            <p>Hello {user_email},</p>
            <p>Multi-Factor Authentication (MFA) has been successfully enabled for your FreshLense account.</p>
            
            <div style="background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #0369a1;">
                    <strong>What this means for you:</strong><br>
                    • Your account is now more secure<br>
                    • You'll receive a verification code via email whenever you log in<br>
                    • Enhanced protection against unauthorized access
                </p>
            </div>
            
            <p>Thank you for taking this important step to secure your account!</p>
            
            <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you didn't enable MFA, please contact our support team immediately.
            </p>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>The FreshLense Security Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    MFA Enabled Successfully
    
    Hello {user_email},
    
    Multi-Factor Authentication (MFA) has been successfully enabled for your FreshLense account.
    
    Your account is now more secure. You'll receive a verification code via email whenever you log in.
    
    Thank you for securing your account!
    
    Best regards,
    The FreshLense Team
    """
    
    return await send_email(user_email, subject, html, text)

async def send_reset_email(to_email: str, reset_token: str, user_email: str):
    """
    Send password reset email.
    """
    reset_url = f"{FRONTEND_URL}/reset-password/{reset_token}"
    
    # DEBUG PRINT
    print(f"\n🔗 DEBUG: FULL RESET URL = {reset_url}\n")
    
    subject = "Reset Your FreshLense Password"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset</h1>
        </div>
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #d97706; margin-top: 0;">Password Reset Request</h2>
            <p>Hello {user_email},</p>
            <p>You have requested to reset your password for your FreshLense account.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    Reset Your Password
                </a>
            </div>
            
            <p style="text-align: center;">
                <small>Or copy and paste this link in your browser:</small><br>
                <code style="background: #f3f4f6; padding: 10px; border-radius: 5px; font-size: 12px; word-break: break-all; display: inline-block; margin-top: 10px;">
                    {reset_url}
                </code>
            </p>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #92400e;">
                    <strong>⚠️ Important:</strong> This link will expire in 1 hour.
                </p>
            </div>
            
            <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you didn't request this password reset, please ignore this email.
            </p>
            
            <p style="margin-top: 30px;">
                Thank you,<br>
                <strong>The FreshLense Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Password Reset Request
    
    Hello {user_email},
    
    You have requested to reset your password for your FreshLense account.
    
    Reset your password by visiting this link:
    {reset_url}
    
    ⚠️ Important: This link will expire in 1 hour.
    
    If you didn't request this password reset, please ignore this email.
    
    Thank you,
    The FreshLense Team
    """
    
    return await send_email(to_email, subject, html, text)

# Alias for backward compatibility
send_password_reset_email = send_reset_email

# Other email functions (not needed for auth.py)
async def send_welcome_email(user_email: str):
    subject = "Welcome to FreshLense!"
    html = f"""
    <html>
    <body>
        <h2>Welcome to FreshLense!</h2>
        <p>Hello {user_email},</p>
        <p>Thank you for joining FreshLense! We're excited to help you monitor and fact-check web content.</p>
        <p>Get started by adding websites to track in your dashboard.</p>
        <p>Best regards,<br>The FreshLense Team</p>
    </body>
    </html>
    """
    return await send_email(user_email, subject, html)

async def send_change_alert_email(user_email: str, page_name: str, change_type: str, page_url: str):
    subject = f"Change Detected: {page_name}"
    html = f"""
    <html>
    <body>
        <h2>Change Detected!</h2>
        <p>Hello {user_email},</p>
        <p>FreshLense has detected a change on one of your monitored pages:</p>
        <p><strong>Page:</strong> {page_name}</p>
        <p><strong>Change Type:</strong> {change_type}</p>
        <p><strong>URL:</strong> {page_url}</p>
        <p>Check your dashboard for details and fact-check results.</p>
        <p>Best regards,<br>The FreshLense Monitoring Team</p>
    </body>
    </html>
    """
    return await send_email(user_email, subject, html)