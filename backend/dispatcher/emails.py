"""
Email utilities for the Dispatcher application, including rider application
rejection notifications with document-specific feedback.
"""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Union
from django.conf import settings

from authentication.emails import send_email_with_fallback

logger = logging.getLogger(__name__)


def get_rider_rejection_email_template(
    rider_name: str,
    reason: str,
    rejected_documents: List[Dict[str, str]],
) -> str:
    """
    Constructs an HTML email template notifying a rider that their application
    has been rejected, listing specific rejected documents and their reasons.
    """
    # Build reason callout section
    reason_section = ""
    if reason and reason.strip():
        reason_section = f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
               style="margin-bottom: 24px; background-color: #FEF2F2; border-left: 4px solid #EF4444; border-radius: 8px;">
            <tr>
                <td style="padding: 18px 20px;">
                    <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #991B1B;">
                        Application Review Note
                    </p>
                    <p style="margin: 0; font-size: 14px; color: #7F1D1D; line-height: 1.6; font-weight: 500;">
                        {reason.strip()}
                    </p>
                </td>
            </tr>
        </table>
        """

    # Build rejected documents section
    docs_section = ""
    if rejected_documents:
        doc_rows = []
        for doc in rejected_documents:
            name = doc.get("name", "Document")
            doc_reason = doc.get("reason", "Requires review and re-submission")
            doc_rows.append(f"""
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="margin-bottom: 12px; border: 1.5px solid #FEE2E2; background-color: #FFFDFD; border-radius: 12px; overflow: hidden;">
                <tr>
                    <td style="width: 44px; padding: 16px 0 16px 16px; vertical-align: top;">
                        <div style="width: 36px; height: 36px; background-color: #FEE2E2; border-radius: 10px; text-align: center; line-height: 36px; font-size: 18px;">
                            📄
                        </div>
                    </td>
                    <td style="padding: 16px 18px 16px 12px; vertical-align: top;">
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                            <tr>
                                <td style="vertical-align: middle;">
                                    <strong style="font-family: 'Outfit', sans-serif; font-size: 15px; color: #141C2E; font-weight: 700;">
                                        {name}
                                    </strong>
                                </td>
                                <td align="right" style="vertical-align: middle;">
                                    <span style="font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 700; color: #DC2626; background-color: #FEF2F2; border: 1px solid #FECACA; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.05em;">
                                        Rejected
                                    </span>
                                </td>
                            </tr>
                        </table>
                        <p style="margin: 8px 0 0 0; font-family: 'Outfit', sans-serif; font-size: 13px; color: #7F1D1D; line-height: 1.5;">
                            <strong style="color: #991B1B;">Reason:</strong> {doc_reason}
                        </p>
                    </td>
                </tr>
            </table>
            """)

        docs_markup = "".join(doc_rows)
        count_label = f" ({len(rejected_documents)})" if len(rejected_documents) > 1 else ""
        docs_section = f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 8px; margin-bottom: 16px;">
            <tr>
                <td style="white-space: nowrap; vertical-align: middle; padding-right: 12px;">
                    <span style="font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #DC2626;">
                        Documents Requiring Re-upload{count_label}
                    </span>
                </td>
                <td width="100%" style="vertical-align: middle;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr><td style="height: 1px; background-color: #FECACA; font-size: 0;">&nbsp;</td></tr>
                    </table>
                </td>
            </tr>
        </table>
        {docs_markup}
        """

    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Application Status Update - Assured Express</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style type="text/css">
    body {{ margin: 0 !important; padding: 0 !important; }}
    img {{ border: 0; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; }}
    table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    @media screen and (max-width: 600px) {{
      .email-shell {{ width: 100% !important; border-radius: 0 !important; }}
      .body-pad {{ padding: 28px 20px !important; }}
      .hero-pad {{ padding: 36px 20px 32px !important; }}
    }}
  </style>
</head>

<body style="margin: 0; padding: 0; background-color: #ECEAE5; font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">

<!-- PREVIEW TEXT -->
<div style="display: none; font-size: 1px; color: #ECEAE5; line-height: 1px; max-height: 0; max-width: 0; opacity: 0; overflow: hidden;">
  Important update regarding your Assured Express rider application and submitted KYC documents.
</div>

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #ECEAE5;">
  <tr>
    <td align="center" style="padding: 36px 16px;">

      <table class="email-shell" role="presentation" width="600" cellspacing="0" cellpadding="0" border="0"
             style="max-width: 600px; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.12); background-color: #FFFFFF;">

        <!-- AMBER TOP BAR -->
        <tr>
          <td style="background-color: #FBB12F; height: 5px; font-size: 0; line-height: 0;">&nbsp;</td>
        </tr>

        <!-- HERO HEADER -->
        <tr>
          <td class="hero-pad" align="center" style="background-color: #141C2E; padding: 44px 40px 36px;">

            <!-- Logo -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 20px;">
              <tr>
                <td align="center" style="background-color: #FBB12F; border-radius: 18px; padding: 2px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                      <td align="center" style="background-color: #141C2E; border-radius: 16px; width: 64px; height: 64px; vertical-align: middle;">
                        <img src="https://res.cloudinary.com/djfz912mh/image/upload/v1773395665/logo2_szdqnh.png"
                             alt="Assured Express" width="52" height="52"
                             style="display: block; width: 52px; height: 52px; border-radius: 10px; margin: 6px auto;">
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <!-- Badge -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 16px;">
              <tr>
                <td align="center" style="border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 100px; padding: 6px 18px; background-color: rgba(239, 68, 68, 0.12);">
                  <span style="font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #FCA5A5;">
                    ✦&nbsp; Application Status Update
                  </span>
                </td>
              </tr>
            </table>

            <!-- Title -->
            <h1 style="font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 800; line-height: 1.25; color: #FFFFFF; margin: 0 0 10px; letter-spacing: -0.5px;">
              Rider Application Update
            </h1>

            <p style="font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 400; color: rgba(255,255,255,0.6); margin: 0 auto; line-height: 1.6; max-width: 420px;">
              Assured Express Delivery Network
            </p>

          </td>
        </tr>

        <!-- BODY -->
        <tr>
          <td class="body-pad" style="background-color: #FFFFFF; padding: 36px 36px 12px;">

            <p style="font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 700; color: #141C2E; margin: 0 0 12px;">
              Hi {rider_name},
            </p>

            <p style="font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 400; color: #4B5563; line-height: 1.7; margin: 0 0 24px;">
              Thank you for applying to join the Assured Express rider network. Our dispatch team has reviewed your application and the documents you submitted.
            </p>

            <p style="font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 400; color: #4B5563; line-height: 1.7; margin: 0 0 24px;">
              At this time, we are unable to approve your application. Please review the details below to understand what needs attention:
            </p>

            {reason_section}

            {docs_section}

            <!-- NEXT STEPS BOX -->
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="margin: 28px 0 24px; border: 1px solid #E2E8F0; background-color: #F8FAFC; border-radius: 14px; overflow: hidden;">
              <tr>
                <td style="padding: 24px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                      <td style="vertical-align: middle;">
                        <h2 style="font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 700; color: #141C2E; margin: 0 0 12px;">
                          How to Re-submit Your Application
                        </h2>
                        <ol style="margin: 0; padding-left: 20px; font-family: 'Outfit', sans-serif; font-size: 14px; color: #475569; line-height: 1.8;">
                          <li>Open the <strong>Assured Express Rider App</strong> on your mobile phone.</li>
                          <li>Log in to your account and go to <strong>Profile &gt; KYC Documents</strong>.</li>
                          <li>Tap on the rejected document(s) to upload a clear, valid, and unexpired replacement.</li>
                          <li>Submit your updated documents — our team will automatically review them.</li>
                        </ol>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <p style="font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 400; color: #64748B; line-height: 1.7; margin: 0 0 28px;">
              If you have any questions or believe this decision was made in error, our support team is available to assist you.
            </p>

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background-color: #0D1424; padding: 32px 36px; text-align: center;">

            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 12px;">
              <tr>
                <td align="center" style="background-color: #FBB12F; border-radius: 12px; padding: 2px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                      <td align="center" style="background-color: #0D1424; border-radius: 10px; width: 40px; height: 40px; vertical-align: middle;">
                        <img src="https://res.cloudinary.com/djfz912mh/image/upload/v1773395665/logo2_szdqnh.png"
                             alt="AX" width="32" height="32"
                             style="display: block; width: 32px; height: 32px; border-radius: 6px; margin: 4px auto;">
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <p style="font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 700; color: #FFFFFF; margin: 0 0 4px;">
              Assured Express
            </p>
            <p style="font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.4); margin: 0 0 20px;">
              Delivering Trust, One Package at a Time
            </p>

            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 20px;">
              <tr>
                <td align="center" style="padding-bottom: 6px;">
                  <a href="mailto:support@axpress.net"
                     style="font-family: 'Outfit', sans-serif; font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.7); text-decoration: none; display: inline-block; padding: 6px 14px; border-radius: 100px; border: 1px solid rgba(255,255,255,0.15);">
                    ✉ &nbsp;support@axpress.net
                  </a>
                </td>
              </tr>
              <tr>
                <td align="center">
                  <a href="tel:+2347070890979"
                     style="font-family: 'Outfit', sans-serif; font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.7); text-decoration: none; display: inline-block; padding: 6px 14px; border-radius: 100px; border: 1px solid rgba(255,255,255,0.15);">
                    📞 &nbsp;+234 707 089 0979
                  </a>
                </td>
              </tr>
            </table>

            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 16px;">
              <tr><td style="height: 1px; background-color: rgba(255,255,255,0.08); font-size: 0;">&nbsp;</td></tr>
            </table>

            <p style="font-family: 'Outfit', sans-serif; font-size: 11px; color: rgba(255,255,255,0.3); line-height: 1.6; margin: 0;">
              © 2026 Assured Express. All rights reserved.<br>
              You are receiving this email because you applied to join Assured Express as a rider.
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


def send_rider_rejection_email(
    rider: Any,
    reason: str = "",
    rejected_doc_ids: Optional[List[Union[str, uuid.UUID]]] = None,
) -> bool:
    """
    Sends an email to a rider notifying them that their application was rejected,
    listing any specific rejected documents along with their rejection reasons.

    Args:
        rider: Either a Rider model instance or rider ID (UUID/str).
        reason (str): Overall application rejection reason.
        rejected_doc_ids (list, optional): List of document UUIDs that were rejected.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    try:
        from dispatcher.models import Rider
        from riders.models import RiderDocument

        # Resolve rider instance
        if not isinstance(rider, Rider):
            try:
                rider = Rider.objects.select_related("user").get(id=rider)
            except Rider.DoesNotExist:
                logger.error(f"send_rider_rejection_email: Rider {rider} not found")
                return False

        user = getattr(rider, "user", None)
        if not user or not user.email:
            logger.warning(
                f"send_rider_rejection_email: Rider {rider.id} has no valid email address."
            )
            return False

        # Determine rider's preferred display name
        rider_name = (
            user.first_name
            or (user.contact_name.split()[0] if user.contact_name else None)
            or user.get_full_name()
            or "Rider"
        )

        # Retrieve rejected documents
        rejected_docs_qs = None
        if rejected_doc_ids:
            rejected_docs_qs = RiderDocument.objects.filter(
                id__in=rejected_doc_ids, rider=rider
            )
        else:
            rejected_docs_qs = RiderDocument.objects.filter(
                rider=rider, status=RiderDocument.Status.REJECTED
            )

        rejected_docs_data: List[Dict[str, str]] = []
        for doc in rejected_docs_qs:
            doc_name = (
                doc.get_doc_type_display()
                or str(doc.doc_type).replace("_", " ").title()
            )
            doc_reason = (
                doc.rejection_reason
                or "Document does not meet verification requirements."
            )
            rejected_docs_data.append({"name": doc_name, "reason": doc_reason})

        # Generate HTML content
        html_content = get_rider_rejection_email_template(
            rider_name=rider_name,
            reason=reason,
            rejected_documents=rejected_docs_data,
        )

        # Generate Plain Text content
        text_lines = [
            f"Hi {rider_name},",
            "",
            "Thank you for applying to join the Assured Express rider network.",
            "Our dispatch team has reviewed your application and submitted onboarding documents.",
            "At this time, we are unable to approve your application.",
        ]

        if reason and reason.strip():
            text_lines.extend(["", f"Reason for Decision: {reason.strip()}"])

        if rejected_docs_data:
            text_lines.extend(["", "Documents Requiring Attention:"])
            for doc in rejected_docs_data:
                text_lines.append(f"- {doc['name']}: {doc['reason']}")

        text_lines.extend([
            "",
            "Next Steps:",
            "1. Open the Assured Express Rider mobile app.",
            "2. Navigate to Profile > KYC Documents.",
            "3. Upload a clear, valid, and unexpired copy of each rejected document.",
            "4. Submit your updated documents for re-review.",
            "",
            "If you have any questions, contact us at support@axpress.net or call +234 707 089 0979.",
            "",
            "Best regards,",
            "The Assured Express Team",
        ])
        text_content = "\n".join(text_lines)

        from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
        from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")

        subject = "Important Update Regarding Your Rider Application - Assured Express"

        return send_email_with_fallback(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_name=from_name,
            from_email=from_email,
        )

    except Exception as e:
        logger.error(
            f"send_rider_rejection_email: Exception sending rejection email to rider: {str(e)}"
        )
        return False
