import json
import resend

from ..config import config


class NotificationService:
    def __init__(self):
        # Initialize Resend client
        resend.api_key = config.RESEND_API_KEY

    def send_notification(self, user_email, subject, body, data=None):
        """Send an email notification to a user"""
        return self._send_resend_notification(user_email, subject, body, data)

    def _send_resend_notification(self, user_email, subject, body, data=None):
        """Send notification using Resend"""
        params: resend.Emails.SendParams = {
            "from": config.EMAIL_FROM,
            "to": [user_email],
            "subject": subject,
            "html": body,
            "text": body,  # Fallback plain text version
        }

        if data:
            params["tags"] = data

        return resend.Emails.send(params)

    def send_bid_notification(self, item_id, bidder_id, amount, seller_email):
        """Send notification for new bid"""
        subject = "New Bid Placed"
        body = f"""
        <h2>New Bid on Your Item</h2>
        <p>Someone has placed a bid of ${amount:.2f} on your item.</p>
        <p>Click here to view the bid details.</p>
        """
        data = {
            "type": "bid",
            "item_id": str(item_id),
            "bidder_id": str(bidder_id),
            "amount": str(amount),
        }
        return self.send_notification(seller_email, subject, body, data)

    def send_like_notification(self, outfit_id, liker_id, creator_email):
        """Send notification for new like"""
        subject = "New Like on Your Outfit"
        body = f"""
        <h2>Your Outfit Got a New Like!</h2>
        <p>Someone liked your outfit. Click here to see who it was.</p>
        """
        data = {"type": "like", "outfit_id": str(outfit_id), "liker_id": str(liker_id)}
        return self.send_notification(creator_email, subject, body, data)


notification_service = NotificationService()
