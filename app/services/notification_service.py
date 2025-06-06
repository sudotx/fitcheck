import logging
import uuid
from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message

from app.config import config
from app.extensions import db, mail, celery
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.models.clothing_item import Item
from app.tasks import send_notification_email_task


class NotificationService:
    def __init__(self):
        """Initialize the notification service."""
        # Flask-Mail is initialized via app.extensions, so no direct initialization here.
        pass

    def send_notification(
        self, user_email: str, subject: str, template_name: str, **kwargs
    ) -> bool:
        """
        Internal method to send an email notification to a user using Flask-Mail.
        This method is intended to be called by Celery tasks, not directly by request handlers.

        Args:
            user_email (str): Recipient email address.
            subject (str): Email subject.
            template_name (str): Name of the HTML template (e.g., "bid_notification" for "emails/bid_notification.html").
            **kwargs: Additional data to pass to the email template.

        Returns:
            bool: True if the email was successfully sent, False otherwise.
        """
        try:
            # Add app URL to template context (assuming APP_BASE_URL in config)
            kwargs["app_url"] = current_app.config.get(
                "APP_BASE_URL", "https://fitcheck.app"
            )
            kwargs["app_name"] = current_app.config.get("APP_NAME", "FitCheck")

            # Render the HTML body of the email using a Jinja2 template
            html_body = render_template(f"emails/{template_name}.html", **kwargs)
            # Create a plain text version as a fallback (optional, but good practice)
            # You might have corresponding .txt templates or strip HTML for this.
            text_body = f"Subject: {subject}\n\n{html_body}"  # Simplified fallback

            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body,
                body=text_body,  # Plain text body as fallback
                sender=current_app.config["MAIL_DEFAULT_SENDER"],
            )

            current_app.logger.info(
                f"Attempting to send email to {user_email} with subject: '{subject}' using template: '{template_name}'"
            )

            mail.send(msg)

            current_app.logger.info(f"Successfully sent email to {user_email}")
            return True

        except Exception as e:
            current_app.logger.error(
                f"Failed to send email to {user_email} for subject '{subject}': {str(e)}",
                exc_info=True,
            )
            return False

    def _create_notification_record(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        item_id: uuid.UUID = None,
        actor_id: uuid.UUID = None,
        metadata: dict = None,
    ) -> Notification:
        """
        Creates and stores a new notification record in the database.
        Then, dispatches a Celery task to send the corresponding email.

        Args:
            user_id (uuid.UUID): The ID of the user who will receive the notification.
            notification_type (NotificationType): The type of notification.
            item_id (uuid.UUID, optional): The ID of the item related to the notification. Defaults to None.
            actor_id (uuid.UUID, optional): The ID of the user who triggered the notification. Defaults to None.
            metadata (dict, optional): Additional JSON metadata for the notification. Defaults to None.

        Returns:
            Notification: The newly created Notification object.
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            item_id=item_id,
            actor_id=actor_id,
            metadata=metadata,
        )
        db.session.add(notification)
        db.session.commit()  # Commit the notification record first
        current_app.logger.info(
            f"Created notification record {notification.id} for user {user_id}, type {notification_type.value}"
        )

        # Dispatch a Celery task to send the email associated with this notification
        send_notification_email_task.delay(str(notification.id))

        return notification

    # --- Public methods to trigger notifications, which now use the DB-first approach ---

    def send_bid_notification(
        self,
        item_id: uuid.UUID,
        bidder_id: uuid.UUID,
        amount: float,
        seller_id: uuid.UUID,
    ):
        """
        Creates a notification for a new bid received on an item.
        This notifies the item seller.
        """
        current_app.logger.info(
            f"Triggering bid received notification for item {item_id} from bidder {bidder_id} for seller {seller_id}"
        )
        self._create_notification_record(
            user_id=seller_id,
            notification_type=NotificationType.BID_RECEIVED,
            item_id=item_id,
            actor_id=bidder_id,
            metadata={
                "amount": float(amount)
            },  # Ensure amount is a basic type for JSON
        )

    def send_outbid_notification(
        self,
        item_id: uuid.UUID,
        outbid_user_id: uuid.UUID,
        new_highest_bid: float,
        new_bidder_id: uuid.UUID,
    ):
        """
        Creates a notification when a user has been outbid.
        """
        current_app.logger.info(
            f"Triggering outbid notification for user {outbid_user_id} on item {item_id}"
        )
        self._create_notification_record(
            user_id=outbid_user_id,
            notification_type=NotificationType.BID_OUTBID,
            item_id=item_id,
            actor_id=new_bidder_id,
            metadata={"new_highest_bid": float(new_highest_bid)},
        )

    def send_auction_won_notification(
        self, item_id: uuid.UUID, winner_id: uuid.UUID, winning_amount: float
    ):
        """
        Creates a notification when a user wins an auction.
        """
        current_app.logger.info(
            f"Triggering auction won notification for user {winner_id} on item {item_id}"
        )
        self._create_notification_record(
            user_id=winner_id,
            notification_type=NotificationType.AUCTION_WON,
            item_id=item_id,
            metadata={"winning_amount": float(winning_amount)},
        )

    def send_auction_expired_notification(
        self, item_id: uuid.UUID, seller_id: uuid.UUID
    ):
        """
        Creates a notification when an auction ends unsold.
        """
        current_app.logger.info(
            f"Triggering auction expired notification for seller {seller_id} on item {item_id}"
        )
        self._create_notification_record(
            user_id=seller_id,
            notification_type=NotificationType.AUCTION_EXPIRED,
            item_id=item_id,
        )

    def send_size_restock_notification(
        self, user_id: uuid.UUID, item_id: uuid.UUID, size_value: str
    ):
        """
        Creates a notification for users who have saved searches for specific sizes when an item
        matching their criteria is restocked or newly listed.
        """
        current_app.logger.info(
            f"Triggering size restock notification for user {user_id} on item {item_id} (size: {size_value})"
        )
        self._create_notification_record(
            user_id=user_id,
            notification_type=NotificationType.SIZE_RESTOCK,
            item_id=item_id,
            metadata={"size_value": size_value},
        )

    def send_outfit_like_notification(
        self, outfit_id: uuid.UUID, liker_id: uuid.UUID, creator_id: uuid.UUID
    ):
        """
        Creates a notification when an outfit receives a new like.
        This notifies the outfit creator.
        """
        current_app.logger.info(
            f"Triggering outfit like notification for outfit {outfit_id} from liker {liker_id} for creator {creator_id}"
        )
        self._create_notification_record(
            user_id=creator_id,
            notification_type=NotificationType.OUTFIT_LIKED,
            # For simplicity, using item_id for outfit_id. Consider a separate outfit_id column in Notification
            item_id=outfit_id,
            actor_id=liker_id,
            metadata={"liker_id": str(liker_id)},
        )

    # --- Methods that send direct emails (not tied to the Notification model, for now) ---

    def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user."""
        try:
            privacy_data = user.get_privacy_data()
            if not privacy_data or not privacy_data.get("email"):
                current_app.logger.error(
                    f"No email found for user {user.username} to send welcome email."
                )
                return False

            return self.send_notification(
                user_email=privacy_data.get("email"),
                subject="Welcome to FitCheck!",
                template_name="welcome",
                username=user.username,
            )
        except Exception as e:
            current_app.logger.error(
                f"Error in send_welcome_email for user {user.id}: {str(e)}",
                exc_info=True,
            )
            return False

    def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email."""
        try:
            privacy_data = user.get_privacy_data()
            if not privacy_data or not privacy_data.get("email"):
                current_app.logger.error(
                    f"No email found for user {user.username} to send password reset email."
                )

            return self.send_notification(
                user_email=privacy_data.get("email"),
                subject="Reset Your Password",
                template_name="reset_password",
                username=user.username,
                reset_token=reset_token,  # This token should contain the necessary info for your frontend
            )
        except Exception as e:
            current_app.logger.error(
                f"Error in send_password_reset_email for user {user.id}: {str(e)}",
                exc_info=True,
            )
            return False

    def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email."""
        try:
            privacy_data = user.get_privacy_data()
            if not privacy_data or not privacy_data.get("email"):
                current_app.logger.error(
                    f"No email found for user {user.username} to send verification email."
                )

            return self.send_notification(
                user_email=privacy_data.get("email"),
                subject="Verify Your Email",
                template_name="verify_email",
                username=user.username,
                verification_token=verification_token,  # This token should contain the necessary info
            )
        except Exception as e:
            current_app.logger.error(
                f"Error in send_verification_email for user {user.id}: {str(e)}",
                exc_info=True,
            )
            return False


# Create a singleton instance of the NotificationService
notification_service = NotificationService()
