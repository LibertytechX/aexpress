"""
Email utilities for sending verification and notification emails via Mailgun.
"""

import os
import requests
import secrets
from django.utils import timezone
from datetime import timedelta
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def send_verification_email(user, otp=None):
    """
    Sends a verification email to the user with a token-based link
    and an optional 6-digit OTP.
    """
    try:
        # Get Mailgun credentials from environment
        api_key = os.getenv("MAILGUN_APIKEY")
        domain = os.getenv("MAILGUN_DOMAIN")
        from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
        from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")
        frontend_url = settings.FRONTEND_URL

        if not api_key or not domain:
            logger.error("Mailgun credentials not configured")
            return False

        # Generate (or get) verification token
        token = generate_verification_token()
        user.email_verification_token = token
        user.email_verification_token_created = timezone.now()
        user.save(update_fields=["email_verification_token", "email_verification_token_created"])

        # Create verification link
        verify_url = f"{frontend_url}/?token={token}"

        # Create HTML email template
        html_content = get_verification_email_template(user.contact_name, verify_url, otp)

        # Create text email content
        text_content = f"Hi {user.contact_name},\n\nWelcome to Assured Express! Please verify your email by visiting: {verify_url}"
        if otp:
            text_content += f"\n\nYour verification code is: {otp}"
        text_content += "\n\nThis link will expire in 24 hours."
        text_content += "\n\nBest regards,\nThe Assured Express Team"

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [user.email],
                "subject": "Welcome to Assured Express - Verify Your Email",
                "html": html_content,
                "text": text_content,
            },
        )

        if response.status_code == 200:
            logger.info(f"Verification email sent to {user.email}")
            return True
        else:
            logger.error(f"Mailgun error: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return False


def get_verification_email_template(name, verify_url, otp=None):
    otp_section = ""
    if otp:
        otp_section = f"""
        <div style="margin: 30px 0; padding: 20px; background-color: #f8fafc; border-radius: 8px; border: 1px dashed #e2e8f0;">
            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Your Verification Code</p>
            <h2 style="margin: 0; color: #1e293b; font-size: 32px; letter-spacing: 4px; font-family: 'Courier New', Courier, monospace;">{otp}</h2>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .button {{
            background-color: #E8A838;
            border: none;
            color: #1B2A4A;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            font-weight: bold;
        }}
    </style>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #1B2A4A; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: #E8A838; margin: 0;">Assured Express</h1>
    </div>
    <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
        <h2>Verify Your Email Address</h2>
        <p>Hi {name},</p>
        <p>Welcome to Assured Express! To complete your registration and start sending deliveries, please verify your email address.</p>

        {otp_section}

        <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" class="button">Verify Email Address</a>
        </div>
        <p>If the button doesn't work, you can also click on this link:</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>Best regards,<br>The Assured Express Team</p>
    </div>
</body>
</html>
"""


def send_password_reset_email(user):
    """
    Send password reset email to user via Mailgun.
    """
    try:
        # Get Mailgun credentials from environment
        api_key = os.getenv("MAILGUN_APIKEY")
        domain = os.getenv("MAILGUN_DOMAIN")
        from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
        from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")
        frontend_url = os.getenv("FRONTEND_URL", "https://aexpress.vercel.app")

        if not api_key or not domain:
            logger.error("Mailgun credentials not configured")
            return False

        # Generate reset token
        token = generate_verification_token()

        # Save token to user
        user.password_reset_token = token
        user.password_reset_token_created = timezone.now()
        user.save(
            update_fields=["password_reset_token", "password_reset_token_created"]
        )

        # Create reset link
        reset_link = f"{frontend_url}/?token={token}&reset=true"

        # Create HTML email template
        html_content = get_password_reset_email_template(
            business_name=user.business_name,
            contact_name=user.contact_name,
            reset_link=reset_link,
        )

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [user.email],
                "subject": "Reset Your Password - Assured Express",
                "html": html_content,
                "text": f"Reset your password by visiting: {reset_link}\n\nThis link will expire in 1 hour.",
            },
        )

        if response.status_code == 200:
            logger.info(f"Password reset email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send password reset email: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False


def get_password_reset_email_template(business_name, contact_name, reset_link):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #1B2A4A 0%, #243656 100%); padding: 40px 32px; text-align: center; border-radius: 16px 16px 0 0;">
                            <div style="width: 60px; height: 60px; margin: 0 auto 16px; background: linear-gradient(135deg, #E8A838 0%, #F5C563 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 32px; font-weight: 800; color: #1B2A4A;">AX</span>
                            </div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">ASSURED EXPRESS</h1>
                            <p style="margin: 8px 0 0; color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 500; letter-spacing: 1px;">MERCHANT PORTAL</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 32px;">
                            <h2 style="margin: 0 0 16px; color: #1B2A4A; font-size: 22px; font-weight: 700;">Reset Your Password</h2>
                            <p style="margin: 0 0 8px; color: #64748b; font-size: 15px; line-height: 1.6;">Hi <strong style="color: #1B2A4A;">{contact_name}</strong>,</p>
                            <p style="margin: 0 0 24px; color: #64748b; font-size: 15px; line-height: 1.6;">We received a request to reset the password for your <strong style="color: #1B2A4A;">{business_name}</strong> merchant account. Click the button below to create a new password:</p>
                            <table role="presentation" style="margin: 0 0 24px;">
                                <tr>
                                    <td style="border-radius: 10px; background: linear-gradient(135deg, #E8A838 0%, #F5C563 100%); box-shadow: 0 4px 12px rgba(232,168,56,0.3);">
                                        <a href="{reset_link}" style="display: inline-block; padding: 14px 32px; color: #1B2A4A; text-decoration: none; font-weight: 700; font-size: 15px; border-radius: 10px;">Reset Password</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0 0 16px; color: #94a3b8; font-size: 13px; line-height: 1.5;">Or copy and paste this link into your browser:</p>
                            <p style="margin: 0 0 24px; padding: 12px; background-color: #f8fafc; border-radius: 8px; word-break: break-all;"><a href="{reset_link}" style="color: #3b82f6; text-decoration: none; font-size: 13px;">{reset_link}</a></p>
                            <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                                <p style="margin: 0; color: #92400E; font-size: 13px; line-height: 1.5;"><strong>⏰ This link expires in 1 hour</strong><br>For security reasons, this link will only work for 1 hour.</p>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 32px; border-radius: 0 0 16px 16px; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 12px; color: #64748b; font-size: 13px; line-height: 1.5;">
                                <strong style="color: #1B2A4A;">Need help?</strong><br>support@axpress.net | +234 809 999 9999
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
