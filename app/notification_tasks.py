from app.extensions import celery
from app.models.notification import Notification
from app.services.notification_service import NotificationService


@celery.task
def send_notification_email_task(notification_id: str):
    """
    Celery task to send an email for a notification.
    This is separated to avoid circular imports.
    """
    notification = Notification.query.get(notification_id)
    if not notification:
        return False

    service = NotificationService()
    # Add your email sending logic here
    return True
