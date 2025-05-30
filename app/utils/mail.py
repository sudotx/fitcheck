import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_email(to, subject, template, **kwargs):
    """
    Send an email using Flask-Mail

    Args:
        to (str): Recipient email address
        subject (str): Email subject
        template (str): Template name to render
        **kwargs: Additional data to pass to the template
    """
    try:
        # Add app URL to template context
        kwargs["app_url"] = current_app.config.get("APP_URL", "https://fitcheck.app")

        msg = Message(
            subject=subject,
            recipients=[to],
            html=render_template(f"emails/{template}.html", **kwargs),
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
        )

        # Log email attempt
        logger.info(f"Attempting to send email to {to} with subject: {subject}")

        # Send email
        mail.send(msg)

        # Log success
        logger.info(f"Successfully sent email to {to}")
        return True

    except Exception as e:
        # Log error
        logger.error(f"Failed to send email to {to}: {str(e)}")
        # Print detailed error for debugging
        print(f"Mail error details: {str(e)}")
        return False


def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        privacy_data = user.get_privacy_data()
        if not privacy_data or not privacy_data.get("email"):
            logger.error(f"No email found for user {user.username}")
            return False

        return send_email(
            to=privacy_data["email"],
            subject="Welcome to FitCheck!",
            template="welcome",
            username=user.username,
        )
    except Exception as e:
        logger.error(f"Error in send_welcome_email: {str(e)}")
        return False


def send_password_reset_email(user, reset_token):
    """Send password reset email"""
    try:
        privacy_data = user.get_privacy_data()
        if not privacy_data or not privacy_data.get("email"):
            logger.error(f"No email found for user {user.username}")
            return False

        return send_email(
            to=privacy_data["email"],
            subject="Reset Your Password",
            template="reset_password",
            username=user.username,
            reset_token=reset_token,
        )
    except Exception as e:
        logger.error(f"Error in send_password_reset_email: {str(e)}")
        return False


def send_verification_email(user, verification_token):
    """Send email verification email"""
    try:
        privacy_data = user.get_privacy_data()
        if not privacy_data or not privacy_data.get("email"):
            logger.error(f"No email found for user {user.username}")
            return False

        return send_email(
            to=privacy_data["email"],
            subject="Verify Your Email",
            template="verify_email",
            username=user.username,
            verification_token=verification_token,
        )
    except Exception as e:
        logger.error(f"Error in send_verification_email: {str(e)}")
        return False
