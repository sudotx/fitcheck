from celery import shared_task
from PIL import Image
import io
from datetime import datetime, timedelta

from .extensions import celery
from .services.ai_service import ai_service
from .models.clothing_item import ClothingItem
from .models.fit import Fit
from .utils.image_handler import upload_to_s3
from .services.notification_service import notification_service
from .models.bid import Bid


@celery.task
def process_uploaded_image(image_data, item_id):
    """Process uploaded image: resize, generate embeddings, and upload to S3"""
    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(image_data))

    # Resize image while maintaining aspect ratio
    max_size = (800, 800)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Convert back to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    # Upload to S3
    image_url = upload_to_s3(img_byte_arr, f"items/{item_id}.jpg")

    # Generate embeddings and tags
    embedding = ai_service.generate_embedding(image)
    tags = ai_service.generate_tags(image)

    # Update item in database
    item = ClothingItem.query.get(item_id)
    if item:
        item.image_url = image_url
        item.embedding_vector = embedding.tolist()
        item.tags.extend(tags)
        item.save()


@celery.task
def update_trending_outfits():
    """Update trending outfits based on likes and comments"""
    # Get outfits from the last 24 hours
    recent_outfits = Fit.query.filter(
        Fit.created_at >= datetime.utcnow() - timedelta(days=1)
    ).all()

    for outfit in recent_outfits:
        # Calculate trending score based on likes and comments
        likes_count = len(outfit.likes)
        comments_count = len(outfit.comments)
        trending_score = (likes_count * 2) + comments_count

        outfit.trending_score = trending_score
        outfit.save()


@celery.task
def cleanup_expired_bids():
    """Clean up expired bids and notify winners"""
    # Get items with expired bidding
    expired_items = ClothingItem.query.filter(
        ClothingItem.bid_end_time < datetime.utcnow(), ClothingItem.status == "active"
    ).all()

    for item in expired_items:
        # Get highest bid
        highest_bid = (
            Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).first()
        )

        if highest_bid:
            # Update item status
            item.status = "sold"
            item.winner_id = highest_bid.user_id
            item.save()

            # Notify winner and seller
            notification_service.send_notification(
                highest_bid.user_id,
                "You won the auction!",
                f"You won the auction for {item.name} with a bid of ${highest_bid.amount:.2f}",
            )

            notification_service.send_notification(
                item.user_id,
                "Your item was sold!",
                f"Your item {item.name} was sold for ${highest_bid.amount:.2f}",
            )
        else:
            # No bids, mark as expired
            item.status = "expired"
            item.save()
