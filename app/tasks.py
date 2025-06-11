import io
import uuid
from datetime import datetime, timedelta

from flask import current_app
from PIL import Image

from .extensions import celery, db
from .models.bid import Bid, BidStatus
from .models.clothing_item import AuctionStatus, Item
from .models.token_blocklist import TokenBlocklist
from .models.user import User
from .services.ai_service import ai_service
from .services.LN_service import lightning_service
from .services.notification_service import (
    Notification,
    NotificationType,
    notification_service,
)
from .utils.image_handler import image_handler


@celery.task
def process_uploaded_image(image_data, item_id):
    """Process uploaded image: resize, generate embeddings, and upload to Cloudinary"""
    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(image_data))

    # Resize image while maintaining aspect ratio
    max_size = (800, 800)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Convert back to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    # Upload to Cloudinary
    image_url = image_handler.upload_to_cloudinary(img_byte_arr, f"images")

    # Generate embeddings and tags
    embedding = ai_service.generate_embedding(image)
    tags = ai_service.generate_tags(image)

    # Update item in database
    item = Item.query.get(item_id)
    if item:
        item.image_url = image_url
        item.embedding_vector = embedding.tolist()
        item.tags.extend(tags)
        item.save()


@celery.task
def cleanup_expired_bids():
    """Clean up expired bids and notify winners"""
    # Get items with expired bidding
    expired_items = Item.query.filter(
        Item.auction_ends_at < datetime.utcnow(), Item.auction_status == "active"
    ).all()

    for item in expired_items:
        # Get highest bid
        highest_bid = (
            Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).first()
        )

        if highest_bid:
            # Update item status
            item.auction_status = AuctionStatus.SOLD
            item.auction_current_bidder_id = highest_bid.user_id
            item.save()

            # Notify winner and seller
            notification_service.send_notification(
                highest_bid.user_id,
                "You won the auction!",
                f"You won the auction for {item.title} with a bid of ${highest_bid.amount:.2f}",
            )

            notification_service.send_notification(
                item.user_id,
                "Your item was sold!",
                f"Your item {item.title} was sold for ${highest_bid.amount:.2f}",
            )
        else:
            # No bids, mark as expired
            item.auction_status = AuctionStatus.EXPIRED
            item.save()


@celery.task
def cleanup_expired_tokens():
    """Clean up expired tokens from the blocklist"""
    # Delete tokens that have expired
    expired_tokens = TokenBlocklist.query.filter(
        TokenBlocklist.expires_at < datetime.utcnow()
    ).all()

    for token in expired_tokens:
        db.session.delete(token)

    db.session.commit()

    return f"Cleaned up {len(expired_tokens)} expired tokens"


@celery.task(
    bind=True, max_retries=5, default_retry_delay=300
)  # Retry after 5 minutes for payment issues
def generate_invoice_for_winning_bid(self, bid_id: str) -> None:
    """
    Celery task to generate a Lightspark invoice for a winning bid.
    This invoice is then sent to the winning bidder for payment.
    """
    try:
        current_app.logger.info(
            f"Attempting to generate invoice for winning bid ID: {bid_id}"
        )
        bid = Bid.query.get(uuid.UUID(bid_id))
        if not bid:
            current_app.logger.error(
                f"Bid {bid_id} not found. Cannot generate invoice."
            )
            return

        if bid.status != BidStatus.PENDING:
            current_app.logger.warning(
                f"Bid {bid_id} is not in PENDING status ({bid.status.value}). Skipping invoice generation."
            )
            return

        item = Item.query.get(bid.item_id)
        if not item:
            current_app.logger.error(
                f"Item {bid.item_id} not found for bid {bid_id}. Cannot generate invoice."
            )
            return

        bidder = User.query.get(bid.user_id)
        if not bidder:
            current_app.logger.error(
                f"Bidder user {bid.user_id} not found for bid {bid_id}. Cannot generate invoice."
            )
            return

        # Ensure lightning_service is initialized
        if not lightning_service._client:
            current_app.logger.error("LightsparkService not initialized. Retrying...")
            raise self.retry(countdown=60)  # Retry after 1 minute

        memo = f"Payment for winning bid on item: {item.title}"
        # Set invoice expiry (e.g., 24 hours for payment)
        # You might want this to be shorter for a real-time auction, e.g., 30 minutes.
        invoice_expiry_secs = 24 * 3600  # 24 hours

        encoded_invoice = lightning_service.create_invoice(
            amount_sats=float(bid.amount),
            memo=memo,
            expiry_secs=invoice_expiry_secs,
        )

        if encoded_invoice:
            bid.encoded_invoice = encoded_invoice
            bid.status = BidStatus.INVOICE_GENERATED
            bid.updated_at = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(
                f"Invoice generated for bid {bid_id}. Encoded invoice: {encoded_invoice}"
            )

            # Notify the winning bidder that an invoice has been generated for them to pay
            notification_service.send_auction_won_notification(
                item_id=bid.item_id,
                winner_id=bid.user_id,
                winning_amount=float(bid.amount),
            )
            # You might also send the encoded_invoice directly to them via email/in-app message
            # For example, by updating the send_auction_won_notification to accept an invoice string
            # or creating a new specific notification type like "invoice_for_winning_bid"

        else:
            bid.status = (
                BidStatus.FAILED_PAYMENT
            )  # Or a more specific status like INVOICE_GENERATION_FAILED
            bid.updated_at = datetime.utcnow()
            db.session.commit()
            current_app.logger.error(f"Failed to generate invoice for bid {bid_id}.")
            # Notify admin or relevant user about the failure
            # Consider retrying this task if it's a transient Lightspark error
            raise self.retry(countdown=300)  # Retry after 5 minutes

    except Exception as e:
        current_app.logger.error(
            f"Error in generate_invoice_for_winning_bid for bid {bid_id}: {e}",
            exc_info=True,
        )
        db.session.rollback()  # Rollback any changes in case of an error
        raise self.retry(exc=e)  # Re-raise for Celery to handle retries


@celery.task(bind=True, max_retries=5, default_retry_delay=300)
def handle_seller_payout(
    self, item_id: str, payout_amount_sats: float, seller_lightning_address: str
) -> None:
    """
    Celery task to send a Lightning payment to the seller's Lightning address.
    This would typically be triggered after a winning bid has been paid.
    """
    try:
        current_app.logger.info(
            f"Attempting payout for item {item_id} to seller with amount {payout_amount_sats} sats."
        )

        # In a real scenario, seller_lightning_address would likely be an LNURL or BOLT11 invoice
        # provided by the seller. For simplicity, assume it's a direct BOLT11 invoice for now.
        # If it's an LNURL, you'd need to resolve it first to get an invoice.

        # Ensure lightning_service is initialized
        if not lightning_service._client:
            current_app.logger.error("LightsparkService not initialized. Retrying...")
            raise self.retry(countdown=60)  # Retry after 1 minute

        # Pay the seller's invoice
        payment = lightning_service.pay_invoice(
            encoded_invoice=seller_lightning_address,  # Assuming seller provides an invoice here
            maximum_fees_sats=50,  # Example max fee
            timeout_secs=300,  # 5 minutes timeout
        )

        if payment and payment.id:
            # You might want to record this outgoing payment in your database
            # e.g., in a new Payout model, or update the Item/Bid with payout_id
            current_app.logger.info(
                f"Payout initiated for item {item_id}. Lightspark Payment ID: {payment.id}, Status: {payment.status}"
            )
            # Consider sending a notification to the seller about the pending/successful payout
        else:
            current_app.logger.error(f"Failed to initiate payout for item {item_id}.")
            raise self.retry(countdown=300)  # Retry after 5 minutes

    except Exception as e:
        current_app.logger.error(
            f"Error in handle_seller_payout for item {item_id}: {e}", exc_info=True
        )
        db.session.rollback()
        raise self.retry(exc=e)


@celery.task
def generate_item_embedding_task(item_id: str) -> None:
    """
    Celery task to asynchronously generate and store an embedding for a specific item.
    It also adds this embedding to the FAISS vector store for similarity searches.

    Args:
        item_id (str): The unique ID of the item to process.
    """
    try:
        print(f"Starting embedding generation for item {item_id}...")
        item = Item.query.get(item_id)
        if not item:
            print(f"Item {item_id} not found for embedding generation. Skipping.")
            return

        # Generate the embedding using the AI service.
        embedding = ai_service.generate_embedding(item.image_url)

        if embedding:
            # Store the embedding (as a list) in the database.
            item.embedding = embedding
            db.session.commit()
            print(f"Embedding for item {item_id} successfully stored in DB.")

            # Add the embedding to the FAISS index for quick similarity lookups.
            # We convert the list embedding to a NumPy array for FAISS compatibility if necessary,
            # though LangChain's FAISS wrapper handles this.
            ai_service.add_to_index(embedding, str(item.id))
        else:
            print(f"Failed to generate embedding for item {item_id}.")
            db.session.rollback()  # Rollback if embedding generation failed but prior changes were made.
    except Exception as e:
        print(
            f"Error in Celery task generate_item_embedding_task for item {item_id}: {e}"
        )
        db.session.rollback()  # Rollback any changes in case of an error


@celery.task
def generate_item_tags_colors_style_task(item_id: str) -> None:
    """
    Celery task to asynchronously generate and store tags, dominant colors,
    and clothing style for a specific item based on its image.

    Args:
        item_id (str): The unique ID of the item to process.
    """
    try:
        print(f"Starting tags, colors, and style generation for item {item_id}...")
        item = Item.query.get(item_id)
        if not item:
            print(f"Item {item_id} not found for tag/color/style generation. Skipping.")
            return

        # Generate tags, colors, and style using the AI service.
        tags = ai_service.generate_tags(item.image_url)
        colors = ai_service.generate_colors(item.image_url)
        style = ai_service.get_clothing_style(item.image_url)

        # Update the item in the database with the generated data.
        item.tags = tags
        item.colors = colors
        item.style = style

        db.session.commit()
        print(f"Successfully generated and stored data for item {item_id}:")
        print(f"  Tags: {tags}")
        print(f"  Colors: {colors}")
        print(f"  Style: {style}")
    except Exception as e:
        print(
            f"Error in Celery task generate_item_tags_colors_style_task for item {item_id}: {e}"
        )
        db.session.rollback()  # Rollback any changes in case of an error


@celery.task
def send_notification_email_task(notification_id: str) -> None:
    """
    Celery task to process a stored Notification record and send an email using Flask-Mail.

    Args:
        notification_id (str): The UUID string of the Notification record to process.
    """
    try:
        current_app.logger.info(
            f"Celery task: Starting email sending for notification ID {notification_id}..."
        )
        # Retrieve the notification from the database
        notification = Notification.query.get(uuid.UUID(notification_id))
        if not notification:
            current_app.logger.warning(
                f"Celery task: Notification {notification_id} not found. Skipping email sending."
            )
            return

        # Fetch the recipient user's email
        recipient_user = User.query.get(notification.user_id)
        if not recipient_user or not recipient_user.email:
            current_app.logger.warning(
                f"Celery task: Recipient user {notification.user_id} not found or has no email. Skipping email sending for notification {notification_id}."
            )
            return

        user_email = recipient_user.email
        subject = "FitCheck Notification"  # Default subject
        template_name = "default_notification"  # Default template
        template_kwargs = {
            "notification_type": notification.type.value,
            "metadata": notification.metadata,
            "notification_id": str(notification.id),
        }

        # Fetch related item details if available
        item_title = None
        item_image_url = None
        if notification.item_id:
            item = Item.query.get(notification.item_id)
            if item:
                item_title = item.title
                item_image_url = item.image_url
                template_kwargs["item"] = (
                    item.to_dict()
                )  # Pass item details to template
                template_kwargs["item_title"] = item_title
                template_kwargs["item_image_url"] = item_image_url
            else:
                current_app.logger.warning(
                    f"Celery task: Item {notification.item_id} not found for notification {notification.id}. Preview will be limited."
                )

        # Fetch related actor details if available
        actor_username = None
        if notification.actor_id:
            actor_user = User.query.get(notification.actor_id)
            if actor_user:
                actor_username = actor_user.username
                template_kwargs["actor"] = (
                    actor_user.to_dict()
                )  # Pass actor details to template
                template_kwargs["actor_username"] = actor_username
            else:
                current_app.logger.warning(
                    f"Celery task: Actor user {notification.actor_id} not found for notification {notification.id}. Preview will be limited."
                )

        # Determine subject and template based on notification type
        if notification.type == NotificationType.BID_RECEIVED:
            subject = f"New Bid on Your Item: {item_title or 'Auction Item'}"
            template_name = "bid_received_notification"
            template_kwargs["amount"] = notification.metadata.get("amount")
            template_kwargs["bidder_username"] = (
                actor_username if actor_username else "Someone"
            )

        elif notification.type == NotificationType.BID_OUTBID:
            subject = f"You've Been Outbid on: {item_title or 'Auction Item'}"
            template_name = "bid_outbid_notification"
            template_kwargs["new_highest_bid"] = notification.metadata.get(
                "new_highest_bid"
            )
            template_kwargs["new_bidder_username"] = (
                actor_username if actor_username else "Someone"
            )

        elif notification.type == NotificationType.AUCTION_WON:
            subject = (
                f"Congratulations! You Won the Auction for: {item_title or 'An Item'}"
            )
            template_name = "auction_won_notification"
            template_kwargs["winning_amount"] = notification.metadata.get(
                "winning_amount"
            )

        elif notification.type == NotificationType.AUCTION_EXPIRED:
            subject = f"Your Auction for {item_title or 'An Item'} Ended Unsold"
            template_name = "auction_expired_notification"

        elif notification.type == NotificationType.SIZE_RESTOCK:
            subject = f"New Item in Your Saved Size: {notification.metadata.get('size_value', 'N/A')}"
            template_name = "size_restock_notification"
            template_kwargs["size_value"] = notification.metadata.get("size_value")

        elif notification.type == NotificationType.OUTFIT_LIKED:
            subject = f"Your Outfit Got a New Like!"
            template_name = "outfit_liked_notification"
            template_kwargs["liker_username"] = (
                actor_username if actor_username else "Someone"
            )
            template_kwargs["outfit_id"] = str(
                notification.item_id
            )  # Using item_id for outfit_id

        # Pass recipient's username if available, useful for personalizing greetings
        if recipient_user.username:
            template_kwargs["recipient_username"] = recipient_user.username

        # Send the email using the service's internal method
        success = notification_service.send_notification(
            user_email=user_email,
            subject=subject,
            template_name=template_name,
            **template_kwargs,
        )

        if success:
            current_app.logger.info(
                f"Celery task: Email for notification {notification_id} successfully sent."
            )
            # Optionally, you could mark the notification as 'email_sent' in the DB here
        else:
            current_app.logger.error(
                f"Celery task: Failed to send email for notification {notification_id}."
            )

    except Exception as e:
        current_app.logger.critical(
            f"Celery task: Unhandled error in send_notification_email_task for notification {notification_id}: {e}",
            exc_info=True,
        )
        # In a real application, you'd implement retry mechanisms or move to a dead-letter queue.
        db.session.rollback()  # Ensure session is rolled back if an error occurs
