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
        user.save(
            update_fields=[
                "email_verification_token",
                "email_verification_token_created",
            ]
        )

        # Create verification link
        verify_url = f"{frontend_url}/?token={token}"

        # Create HTML email template
        html_content = get_verification_email_template(
            user.contact_name, verify_url, otp
        )

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

        if user.usertype == "Dispatcher":
            frontend_url = os.getenv("DISPATCHER_FRONTEND_URL", "http://localhost:5174")
            portal_name = "DISPATCHER PORTAL"
        else:
            frontend_url = os.getenv("FRONTEND_URL", "https://aexpress.vercel.app")
            portal_name = "MERCHANT PORTAL"

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
            business_name=user.business_name or "Assured Express",
            contact_name=user.contact_name or user.get_full_name(),
            reset_link=reset_link,
            portal_name=portal_name,
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


def get_password_reset_email_template(
    business_name, contact_name, reset_link, portal_name="MERCHANT PORTAL"
):
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
                            <p style="margin: 8px 0 0; color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 500; letter-spacing: 1px;">{portal_name}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 32px;">
                            <h2 style="margin: 0 0 16px; color: #1B2A4A; font-size: 22px; font-weight: 700;">Reset Your Password</h2>
                            <p style="margin: 0 0 8px; color: #64748b; font-size: 15px; line-height: 1.6;">Hi <strong style="color: #1B2A4A;">{contact_name}</strong>,</p>
                            <p style="margin: 0 0 24px; color: #64748b; font-size: 15px; line-height: 1.6;">We received a request to reset the password for your <strong style="color: #1B2A4A;">{business_name}</strong> account. Click the button below to create a new password:</p>
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


def send_mobile_password_reset_email(user, otp):
    """
    Send OTP-based password reset email to user via Mailgun for the mobile app.
    """
    try:
        # Get Mailgun credentials from environment
        api_key = os.getenv("MAILGUN_APIKEY")
        domain = os.getenv("MAILGUN_DOMAIN")
        from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
        from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")

        if not api_key or not domain:
            logger.error("Mailgun credentials not configured")
            return False

        # Create HTML email template
        html_content = get_mobile_password_reset_email_template(
            business_name=user.business_name or "Assured Express",
            contact_name=user.contact_name or user.get_full_name(),
            otp=otp,
            portal_name="MOBILE APP",
        )

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [user.email],
                "subject": "Your Password Reset Code - Assured Express",
                "html": html_content,
                "text": f"Your password reset code is: {otp}\n\nThis code will expire in 10 minutes.",
            },
        )

        if response.status_code == 200:
            logger.info(f"Mobile password reset email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send mobile password reset email: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending mobile password reset email: {str(e)}")
        return False


def get_mobile_password_reset_email_template(
    business_name, contact_name, otp, portal_name="MOBILE APP"
):
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
                            <p style="margin: 8px 0 0; color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 500; letter-spacing: 1px;">{portal_name}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 32px;">
                            <h2 style="margin: 0 0 16px; color: #1B2A4A; font-size: 22px; font-weight: 700;">Reset Your Password</h2>
                            <p style="margin: 0 0 8px; color: #64748b; font-size: 15px; line-height: 1.6;">Hi <strong style="color: #1B2A4A;">{contact_name}</strong>,</p>
                            <p style="margin: 0 0 24px; color: #64748b; font-size: 15px; line-height: 1.6;">We received a request to reset the password for your <strong style="color: #1B2A4A;">{business_name}</strong> account. Please use the following code to reset your password:</p>
                            
                            <div style="margin: 30px 0; padding: 24px; background-color: #f8fafc; border-radius: 12px; border: 2px dashed #94a3b8; text-align: center;">
                                <p style="margin: 0 0 12px 0; color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">Your Reset Code</p>
                                <h2 style="margin: 0; color: #1B2A4A; font-size: 42px; letter-spacing: 8px; font-family: 'Courier New', Courier, monospace; font-weight: 800;">{otp}</h2>
                            </div>
                            
                            <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                                <p style="margin: 0; color: #92400E; font-size: 13px; line-height: 1.5;"><strong>⏰ This code expires in 10 minutes</strong><br>For security reasons, this code will only work for 10 minutes.</p>
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


def send_onboarding_email(user):
    """
    Sends a premium onboarding email to the user after successful OTP verification.
    """
    try:
        # Get Mailgun credentials from environment
        api_key = os.getenv("MAILGUN_APIKEY")
        domain = os.getenv("MAILGUN_DOMAIN")
        from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
        from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")

        if not api_key or not domain:
            logger.error("Mailgun credentials not configured")
            return False

        # Create HTML email template
        # Use first_name if available, else contact_name
        first_name = user.first_name or (
            user.contact_name.split()[0] if user.contact_name else "Merchant"
        )
        html_content = get_onboarding_email_template(first_name)

        # Create text email content
        text_content = f"Hi {first_name},\n\nWelcome to Assured Express! We're thrilled to have you on board. Your account is live and your dashboard is ready — you can start requesting deliveries right now.\n\nBest regards,\nThe Assured Express Team"

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [user.email],
                "subject": "Welcome to Assured Express 🎉",
                "html": html_content,
                "text": text_content,
            },
        )

        if response.status_code == 200:
            logger.info(f"Onboarding email sent to {user.email}")
            return True
        else:
            logger.error(f"Mailgun error sending onboarding email: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending onboarding email: {str(e)}")
        return False


def get_onboarding_email_template(name):
    """
    Returns the HTML template for the onboarding email.
    """
    return f"""
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="format-detection" content="telephone=no,address=no,email=no,date=no,url=no">
  <title>Welcome to Assured Express 🎉</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style type="text/css">
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');
    body {{ margin: 0 !important; padding: 0 !important; }}
    img {{ border: 0; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; }}
    table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    @media screen and (max-width: 600px) {{
      .email-shell   {{ width: 100% !important; border-radius: 0 !important; }}
      .mobile-pad    {{ padding: 32px 24px !important; }}
      .mobile-h1     {{ font-size: 28px !important; }}
      .hero-pad      {{ padding: 44px 24px 36px !important; }}
      .feat-row td   {{ display: block !important; width: 100% !important; }}
      .cta-btn       {{ padding: 15px 32px !important; font-size: 15px !important; }}
      .footer-pad    {{ padding: 32px 24px 28px !important; }}
    }}
  </style>
</head>

<body style="margin:0;padding:0;background-color:#ECEAE5;font-family:'Outfit',sans-serif;">

<!-- HIDDEN PREVIEW TEXT -->
<div style="display:none;font-size:1px;color:#ECEAE5;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
  You're officially part of a smarter, safer delivery network. Welcome aboard! 🎉&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</div>

<!-- PAGE WRAPPER -->
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#ECEAE5;">
<tr><td align="center" style="padding:36px 16px;">

  <!-- [EMAIL CARD] -->
  <table class="email-shell" role="presentation" width="600" cellspacing="0" cellpadding="0" border="0"
    style="max-width:600px;border-radius:24px;overflow:hidden;box-shadow:0 12px 48px rgba(0,0,0,0.14);">


    <!-- AMBER TOP BAR -->
    <tr>
      <td style="background-color:#FBB12F;height:5px;font-size:0;line-height:0;">&nbsp;</td>
    </tr>


    <!-- HERO HEADER -->
    <tr>
      <td class="hero-pad" align="center" style="background-color:#141C2E;padding:56px 48px 48px;">

        <!-- Logo -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 auto 32px;">
          <tr>
            <td align="center" style="background-color:#FBB12F;border-radius:22px;padding:3px;line-height:0;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="background-color:#141C2E;border-radius:19px;width:94px;height:94px;vertical-align:middle;">
                    <img src="https://res.cloudinary.com/djfz912mh/image/upload/v1773395665/logo2_szdqnh.png"
                         alt="Assured Express" width="80" height="80"
                         style="display:block;width:80px;height:80px;border-radius:14px;margin:7px auto;">
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- Badge -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 auto 22px;">
          <tr>
            <td align="center" style="border:1px solid rgba(251,177,47,0.45);border-radius:100px;padding:6px 18px;background-color:rgba(251,177,47,0.1);">
              <span style="font-family:'Outfit',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;color:#FBB12F;">
                ✦&nbsp; Account Activated
              </span>
            </td>
          </tr>
        </table>

        <!-- H1 -->
        <h1 class="mobile-h1" style="font-family:'Outfit',sans-serif;font-size:38px;font-weight:800;line-height:1.18;color:#FFFFFF;margin:0 0 16px;letter-spacing:-0.8px;">
          Welcome to<br>
          <span style="color:#FBB12F;">Assured</span> Express
        </h1>

        <!-- Subtitle -->
        <p style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:400;color:rgba(255,255,255,0.55);margin:0 auto;line-height:1.75;max-width:380px;">
          Nigeria's trusted logistics partner for merchants who care about getting goods to customers safely and on time.
        </p>

      </td>
    </tr>


    <!-- BODY -->
    <tr>
      <td class="mobile-pad" style="background-color:#FFFFFF;padding:48px 44px 0;">

        <!-- Greeting -->
        <p style="font-family:'Outfit',sans-serif;font-size:21px;font-weight:700;color:#141C2E;margin:0 0 12px;">
          Hi {name}, 👋
        </p>
        <p style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:400;color:#5A6680;line-height:1.85;margin:0 0 40px;">
          We're thrilled to have you on board! Your account is live and your dashboard is ready — you can start requesting deliveries right now. Here's everything at your fingertips:
        </p>

        <!-- Section label row -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:18px;">
          <tr>
            <td style="white-space:nowrap;vertical-align:middle;padding-right:12px;">
              <span style="font-family:'Outfit',sans-serif;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.16em;color:#A0AABB;">What you can do right now</span>
            </td>
            <td width="100%" style="vertical-align:middle;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr><td style="height:2px;background-color:#FBB12F;border-radius:2px;opacity:0.35;font-size:0;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- FEATURE 1 -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="margin-bottom:10px;border-radius:16px;border:1.5px solid #EEF2FA;background-color:#F8FAFF;overflow:hidden;">
          <tr>
            <td style="width:72px;padding:20px 0 20px 18px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:46px;height:46px;background-color:#FBB12F;border-radius:13px;font-size:22px;line-height:46px;text-align:center;vertical-align:middle;">
                    🚀
                  </td>
                </tr>
              </table>
            </td>
            <td style="padding:20px 12px;vertical-align:middle;">
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#141C2E;margin:0 0 4px;">Request a Delivery in Minutes</p>
              <p style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:400;color:#6B7A99;margin:0;line-height:1.65;">Log in and dispatch your first order — it takes less than 2 minutes to get started.</p>
            </td>
            <td style="width:38px;padding-right:16px;text-align:center;vertical-align:middle;">
              <span style="font-family:sans-serif;font-size:20px;font-weight:700;color:#FBB12F;">›</span>
            </td>
          </tr>
        </table>

        <!-- FEATURE 2 -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="margin-bottom:10px;border-radius:16px;border:1.5px solid #EEF2FA;background-color:#F8FAFF;overflow:hidden;">
          <tr>
            <td style="width:72px;padding:20px 0 20px 18px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:46px;height:46px;background-color:#00B67A;border-radius:13px;font-size:22px;line-height:46px;text-align:center;vertical-align:middle;">
                    📍
                  </td>
                </tr>
              </table>
            </td>
            <td style="padding:20px 12px;vertical-align:middle;">
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#141C2E;margin:0 0 4px;">Real-Time Shipment Tracking</p>
              <p style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:400;color:#6B7A99;margin:0;line-height:1.65;">Follow every package from pickup to doorstep — live, accurate, and fully transparent.</p>
            </td>
            <td style="width:38px;padding-right:16px;text-align:center;vertical-align:middle;">
              <span style="font-family:sans-serif;font-size:20px;font-weight:700;color:#00B67A;">›</span>
            </td>
          </tr>
        </table>

        <!-- FEATURE 3 -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="margin-bottom:10px;border-radius:16px;border:1.5px solid #EEF2FA;background-color:#F8FAFF;overflow:hidden;">
          <tr>
            <td style="width:72px;padding:20px 0 20px 18px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:46px;height:46px;background-color:#141C2E;border-radius:13px;font-size:22px;line-height:46px;text-align:center;vertical-align:middle;">
                    🌍
                  </td>
                </tr>
              </table>
            </td>
            <td style="padding:20px 12px;vertical-align:middle;">
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#141C2E;margin:0 0 4px;">Reach Customers Everywhere</p>
              <p style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:400;color:#6B7A99;margin:0;line-height:1.65;">Lagos and beyond — we handle the last mile so your customers always get their orders.</p>
            </td>
            <td style="width:38px;padding-right:16px;text-align:center;vertical-align:middle;">
              <span style="font-family:sans-serif;font-size:20px;font-weight:700;color:#141C2E;">›</span>
            </td>
          </tr>
        </table>

        <!-- FEATURE 4 -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="border-radius:16px;border:1.5px solid #EEF2FA;background-color:#F8FAFF;overflow:hidden;">
          <tr>
            <td style="width:72px;padding:20px 0 20px 18px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:46px;height:46px;background-color:#FBB12F;border-radius:13px;font-size:22px;line-height:46px;text-align:center;vertical-align:middle;">
                    💬
                  </td>
                </tr>
              </table>
            </td>
            <td style="padding:20px 12px;vertical-align:middle;">
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#141C2E;margin:0 0 4px;">Dedicated Merchant Support</p>
              <p style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:400;color:#6B7A99;margin:0;line-height:1.65;">Our support team is always ready to help you — any time, any issue, any question.</p>
            </td>
            <td style="width:38px;padding-right:16px;text-align:center;vertical-align:middle;">
              <span style="font-family:sans-serif;font-size:20px;font-weight:700;color:#FBB12F;">›</span>
            </td>
          </tr>
        </table>

      </td>
    </tr>


    <!-- CTA BLOCK -->
    <tr>
      <td class="mobile-pad" style="background-color:#FFFFFF;padding:36px 44px;">

        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="border-radius:20px;overflow:hidden;">
          <tr>
            <td style="width:6px;background-color:#FBB12F;">&nbsp;</td>
            <td align="center" style="background-color:#141C2E;padding:40px 36px;">
              <div style="font-size:42px;line-height:1;margin-bottom:16px;">🎯</div>
              <h2 style="font-family:'Outfit',sans-serif;font-size:22px;font-weight:800;color:#FFFFFF;margin:0 0 10px;letter-spacing:-0.3px;">
                Your dashboard is <span style="color:#FBB12F;">ready.</span>
              </h2>
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:400;color:rgba(255,255,255,0.5);margin:0 auto 30px;line-height:1.75;max-width:340px;">
                Log in now and request your first delivery in under 2 minutes.<br>Your customers are waiting!
              </p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 auto;">
                <tr>
                  <td align="center" style="border-radius:100px;background-color:#FBB12F;">
                    <a href="https://send.axpress.net" target="_blank" class="cta-btn"
                      style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:700;color:#141C2E;text-decoration:none;display:inline-block;padding:17px 48px;border-radius:100px;letter-spacing:0.02em;">
                      Go to My Dashboard &nbsp;→
                    </a>
                  </td>
                </tr>
              </table>
              <p style="font-family:'Outfit',sans-serif;font-size:11px;color:rgba(255,255,255,0.25);margin:20px 0 0;letter-spacing:0.06em;">
                🔒 &nbsp;SECURE &nbsp;·&nbsp; TRUSTED &nbsp;·&nbsp; ALWAYS ON
              </p>
            </td>
          </tr>
        </table>

      </td>
    </tr>


    <!-- SUPPORT STRIP -->
    <tr>
      <td class="mobile-pad" style="background-color:#FFFFFF;padding:0 44px 36px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="border-radius:16px;background-color:#F0FBF6;border:1.5px solid #C2EDD8;overflow:hidden;">
          <tr>
            <td style="width:70px;padding:18px 0 18px 18px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:44px;height:44px;background-color:#00B67A;border-radius:12px;font-size:22px;line-height:44px;text-align:center;vertical-align:middle;">
                    🛟
                  </td>
                </tr>
              </table>
            </td>
            <td style="padding:18px 12px;vertical-align:middle;">
              <p style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#141C2E;margin:0 0 3px;">We're here whenever you need us</p>
              <p style="font-family:'Outfit',sans-serif;font-size:13px;color:#6B7A99;margin:0;line-height:1.55;">Reach out anytime — we love hearing from our merchants.</p>
            </td>
            <td style="width:80px;padding-right:16px;text-align:right;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin-left:auto;">
                <tr>
                  <td style="background-color:#D3F5E6;border:1px solid #A2E6C4;border-radius:100px;padding:5px 11px;">
                    <span style="font-family:'Outfit',sans-serif;font-size:11px;font-weight:700;color:#007A52;">● Online</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>


    <!-- CLOSING MESSAGE -->
    <tr>
      <td class="mobile-pad" style="background-color:#FFFFFF;padding:0 44px 48px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:28px;">
          <tr><td style="height:1px;background-color:#EEF2FA;font-size:0;line-height:0;">&nbsp;</td></tr>
        </table>
        <p style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:400;color:#5A6680;line-height:1.85;margin:0 0 18px;">
          If you have any questions or need help getting started, don't hesitate to reach out — we're here for you every step of the way.
        </p>
        <p style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:400;color:#5A6680;line-height:1.85;margin:0 0 30px;">
          Welcome to the <strong style="color:#141C2E;font-weight:700;">Assured Express family!</strong> 🎉
        </p>
        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
          <tr>
            <td style="width:52px;padding-right:14px;vertical-align:middle;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="width:46px;height:46px;background-color:#FBB12F;border-radius:13px;font-size:22px;line-height:46px;text-align:center;vertical-align:middle;">
                    ✉️
                  </td>
                </tr>
              </table>
            </td>
            <td style="vertical-align:middle;">
              <strong style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:700;color:#141C2E;display:block;line-height:1.4;">The Assured Express Team</strong>
              <span style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:400;color:#A0AABB;">Nigeria's Trusted Logistics Partner</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>


    <!-- FOOTER -->
    <tr>
      <td style="background-color:#0D1424;padding:0;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
          <tr><td style="background-color:#FBB12F;height:3px;font-size:0;line-height:0;">&nbsp;</td></tr>
        </table>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
          <tr>
            <td class="footer-pad" align="center" style="padding:40px 44px 36px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 auto 14px;">
                <tr>
                  <td align="center" style="background-color:#FBB12F;border-radius:16px;padding:2px;line-height:0;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td align="center" style="background-color:#0D1424;border-radius:14px;width:56px;height:56px;vertical-align:middle;">
                          <img src="https://res.cloudinary.com/djfz912mh/image/upload/v1773395665/logo2_szdqnh.png"
                               alt="AX" width="46" height="46"
                               style="display:block;width:46px;height:46px;border-radius:10px;margin:5px auto;">
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <p style="font-family:'Outfit',sans-serif;font-size:18px;font-weight:800;color:#FFFFFF;margin:0 0 4px;letter-spacing:-0.3px;">
                Assured Express
              </p>
              <p style="font-family:'Outfit',sans-serif;font-size:11px;font-weight:400;text-transform:uppercase;letter-spacing:0.12em;color:rgba(255,255,255,0.3);margin:0 0 28px;">
                Delivering Trust, One Package at a Time
              </p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 auto 28px;">
                <tr>
                  <td align="center" style="padding-bottom:8px;">
                    <a href="tel:+2347070890979"
                      style="font-family:'Outfit',sans-serif;font-size:12px;font-weight:500;color:rgba(255,255,255,0.55);text-decoration:none;display:inline-block;padding:7px 18px;border-radius:100px;border:1px solid rgba(255,255,255,0.14);">
                      📞 &nbsp;+234 707 089 0979
                    </a>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:8px;">
                    <a href="mailto:support@axpress.net" style="font-family:'Outfit',sans-serif;font-size:12px;font-weight:500;color:rgba(255,255,255,0.55);text-decoration:none;display:inline-block;padding:7px 18px;border-radius:100px;border:1px solid rgba(255,255,255,0.14);">
                      ✉ &nbsp;support@axpress.net
                    </a>
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <a href="https://send.axpress.net" target="_blank"
                      style="font-family:'Outfit',sans-serif;font-size:12px;font-weight:500;color:rgba(255,255,255,0.55);text-decoration:none;display:inline-block;padding:7px 18px;border-radius:100px;border:1px solid rgba(255,255,255,0.14);">
                      🌐 &nbsp;send.axpress.net
                    </a>
                  </td>
                </tr>
              </table>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:20px;">
                <tr><td style="height:1px;background-color:rgba(255,255,255,0.08);font-size:0;line-height:0;">&nbsp;</td></tr>
              </table>
              <p style="font-family:'Outfit',sans-serif;font-size:11px;color:rgba(255,255,255,0.22);line-height:1.9;margin:0;">
                © 2025 Assured Express. All rights reserved.<br>
                You're receiving this because you created a merchant account on Assured Express.<br>
                <a href="#" style="color:rgba(251,177,47,0.5);text-decoration:none;">Unsubscribe</a>
                &nbsp;·&nbsp;
                <a href="#" style="color:rgba(251,177,47,0.5);text-decoration:none;">Privacy Policy</a>
                &nbsp;·&nbsp;
                <a href="#" style="color:rgba(251,177,47,0.5);text-decoration:none;">Terms</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</td></tr>
</table>
</body>
</html>
"""
