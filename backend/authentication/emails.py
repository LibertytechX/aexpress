"""
Email utilities for sending verification and notification emails via Mailgun.
"""
import os
import requests
import secrets
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def send_verification_email(user):
    """
    Send email verification email to user via Mailgun.

    Args:
        user: User instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get Mailgun credentials from environment
        api_key = os.getenv('MAILGUN_API_KEY')
        domain = os.getenv('MAILGUN_DOMAIN')
        from_email = os.getenv('MAILGUN_FROM_EMAIL', 'noreply@mg.axpress.net')
        from_name = os.getenv('MAILGUN_FROM_NAME', 'Assured Express')
        frontend_url = os.getenv('FRONTEND_URL', 'https://aexpress.vercel.app')

        if not api_key or not domain:
            logger.error("Mailgun credentials not configured")
            return False

        # Generate verification token
        token = generate_verification_token()

        # Save token to user
        user.email_verification_token = token
        user.email_verification_token_created = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_token_created'])

        # Create verification link
        verification_link = f"{frontend_url}/verify-email?token={token}"

        # Create HTML email template
        html_content = get_verification_email_template(
            business_name=user.business_name,
            contact_name=user.contact_name,
            verification_link=verification_link
        )

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [user.email],
                "subject": "Welcome to Assured Express - Verify Your Email",
                "html": html_content,
                "text": f"Welcome to Assured Express! Please verify your email by visiting: {verification_link}"
            }
        )

        if response.status_code == 200:
            logger.info(f"Verification email sent successfully to {user.email}")
            return True
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False


def get_verification_email_template(business_name, contact_name, verification_link):
    """
    Generate beautiful HTML email template for email verification.

    Args:
        business_name: User's business name
        contact_name: User's contact name
        verification_link: Email verification URL

    Returns:
        str: HTML email content
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Assured Express</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f1f5f9; padding: 40px 20px;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

                    <!-- Header with Branding -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1B2A4A 0%, #243656 100%); padding: 40px 40px 30px; text-align: center;">
                            <div style="display: inline-block; background: linear-gradient(135deg, #E8A838, #F5C563); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
                                <span style="font-size: 24px; font-weight: 800; color: #1B2A4A; letter-spacing: 1px;">AX</span>
                            </div>
                            <h1 style="color: #ffffff; font-size: 28px; font-weight: 700; margin: 0 0 8px; letter-spacing: 0.5px;">ASSURED EXPRESS</h1>
                            <p style="color: #E8A838; font-size: 12px; font-weight: 600; letter-spacing: 2px; margin: 0;">MERCHANT PORTAL</p>
                        </td>
                    </tr>

                    <!-- Welcome Message -->
                    <tr>
                        <td style="padding: 40px 40px 30px;">
                            <h2 style="color: #1B2A4A; font-size: 24px; font-weight: 700; margin: 0 0 16px;">Welcome to Assured Express! 🎉</h2>
                            <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 12px;">Hi <strong style="color: #1B2A4A;">{contact_name}</strong>,</p>
                            <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 12px;">
                                Thank you for creating your merchant account with <strong style="color: #1B2A4A;">{business_name}</strong>.
                                We're excited to help you streamline your delivery operations across Lagos!
                            </p>
                            <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                                To get started and unlock all features, please verify your email address by clicking the button below:
                            </p>
                        </td>
                    </tr>

                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 40px 30px; text-align: center;">
                            <a href="{verification_link}" style="display: inline-block; background: linear-gradient(135deg, #E8A838, #F5C563); color: #1B2A4A; text-decoration: none; padding: 16px 48px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(232,168,56,0.3);">
                                ✓ Verify Email Address
                            </a>
                        </td>
                    </tr>

                    <!-- Alternative Link -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0; text-align: center;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 8px 0 0; text-align: center;">
                                <a href="{verification_link}" style="color: #E8A838; font-size: 12px; word-break: break-all;">{verification_link}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Info Box -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <div style="background-color: #FFF8EC; border-left: 4px solid #E8A838; padding: 16px 20px; border-radius: 8px;">
                                <p style="color: #92400e; font-size: 14px; font-weight: 600; margin: 0 0 8px;">📌 Important Note</p>
                                <p style="color: #78350f; font-size: 13px; line-height: 1.6; margin: 0;">
                                    Email verification is optional but recommended for account security and to receive important updates about your deliveries.
                                    You can start using your account immediately without verifying.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Features Preview -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h3 style="color: #1B2A4A; font-size: 18px; font-weight: 700; margin: 0 0 16px;">What You Can Do Now:</h3>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="color: #10b981; font-size: 16px; margin-right: 8px;">✓</span>
                                        <span style="color: #64748b; font-size: 14px;">Create and track delivery orders</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="color: #10b981; font-size: 16px; margin-right: 8px;">✓</span>
                                        <span style="color: #64748b; font-size: 14px;">Fund your wallet and manage payments</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="color: #10b981; font-size: 16px; margin-right: 8px;">✓</span>
                                        <span style="color: #64748b; font-size: 14px;">Access real-time delivery tracking</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="color: #10b981; font-size: 16px; margin-right: 8px;">✓</span>
                                        <span style="color: #64748b; font-size: 14px;">View transaction history and reports</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Divider -->
                    <tr>
                        <td style="padding: 0 40px;">
                            <div style="height: 1px; background-color: #e2e8f0;"></div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center;">
                            <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 12px;">
                                Need help? Contact our support team:
                            </p>
                            <p style="margin: 0 0 8px;">
                                <a href="mailto:support@axpress.net" style="color: #E8A838; text-decoration: none; font-size: 14px; font-weight: 600;">support@axpress.net</a>
                            </p>
                            <p style="margin: 0 0 20px;">
                                <a href="tel:+2348099999999" style="color: #E8A838; text-decoration: none; font-size: 14px; font-weight: 600;">+234 809 999 9999</a>
                            </p>
                            <p style="color: #cbd5e1; font-size: 12px; margin: 0 0 8px;">
                                © 2024 Assured Express. All rights reserved.
                            </p>
                            <p style="color: #cbd5e1; font-size: 11px; margin: 0;">
                                Lagos, Nigeria | www.axpress.net
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

