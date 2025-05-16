import json
import requests
from firebase_admin import credentials, messaging, initialize_app

from ..config import Config


class NotificationService:
    def __init__(self):
        # Initialize Firebase if credentials are available
        if Config.FIREBASE_CREDENTIALS:
            cred = credentials.Certificate(json.loads(Config.FIREBASE_CREDENTIALS))
            initialize_app(cred)
            self.use_firebase = True
        else:
            self.use_firebase = False

    def send_notification(self, user_id, title, body, data=None):
        """Send a push notification to a user"""
        if self.use_firebase:
            return self._send_firebase_notification(user_id, title, body, data)
        else:
            return self._send_onesignal_notification(user_id, title, body, data)

    def _send_firebase_notification(self, user_id, title, body, data=None):
        """Send notification using Firebase Cloud Messaging"""
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=user_id,  # Assuming user_id is the FCM token
        )
        return messaging.send(message)

    def _send_onesignal_notification(self, user_id, title, body, data=None):
        """Send notification using OneSignal"""
        headers = {
            "Authorization": f"Basic {Config.ONESIGNAL_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "app_id": Config.ONESIGNAL_APP_ID,
            "include_player_ids": [user_id],
            "contents": {"en": body},
            "headings": {"en": title},
            "data": data or {},
        }

        response = requests.post(
            "https://onesignal.com/api/v1/notifications", headers=headers, json=payload
        )
        return response.json()

    def send_bid_notification(self, item_id, bidder_id, amount):
        """Send notification for new bid"""
        title = "New Bid Placed"
        body = f"Someone bid ${amount:.2f} on your item"
        data = {
            "type": "bid",
            "item_id": str(item_id),
            "bidder_id": str(bidder_id),
            "amount": str(amount),
        }
        return self.send_notification(item_id, title, body, data)

    def send_like_notification(self, outfit_id, liker_id):
        """Send notification for new like"""
        title = "New Like"
        body = "Someone liked your outfit"
        data = {"type": "like", "outfit_id": str(outfit_id), "liker_id": str(liker_id)}
        return self.send_notification(outfit_id, title, body, data)


notification_service = NotificationService()
