from datetime import datetime, timedelta
from sqlalchemy import UUID, Index
from sqlalchemy.dialects.postgresql import ARRAY
from app.extensions import db
import uuid
import hashlib

from app.services.ai_service import ai_service


class VisualSearchCache(db.Model):
    __tablename__ = "visual_search_cache"

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Content Identification
    image_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # AI Data
    clip_vector = db.Column(
        ARRAY(db.Float(32)), nullable=False  # 32-bit floats for space efficiency
    )
    dominant_colors = db.Column(ARRAY(db.String(7)), nullable=False)  # Hex color codes

    # Search Results
    matched_item_ids = db.Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    match_scores = db.Column(
        ARRAY(db.Float(32)),  # Similarity scores parallel to matched_item_ids
        nullable=False,
        default=[],
    )

    # Cache Management
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=1),
        nullable=False,
        index=True,
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_image_hash_clip", "image_hash", "clip_vector", postgresql_using="hnsw"
        ),  # For vector search
        Index(
            "idx_expires_at",
            "expires_at",
            postgresql_where=db.text("expires_at < NOW()"),
        ),  # For efficient cleanup
    )

    @classmethod
    def create_from_image(cls, image_bytes):
        """Generate cache entry from image data"""
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        # In practice you'd call your AI service here
        clip_vector = ai_service.generate_embedding(image_bytes)
        dominant_colors = ai_service.generate_colors(image_bytes)

        return cls(
            image_hash=image_hash,
            clip_vector=clip_vector,
            dominant_colors=dominant_colors,
        )

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def update_matches(self, item_ids, scores):
        """Store search results with similarity scores"""
        self.matched_item_ids = item_ids
        self.match_scores = scores
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # Refresh TTL
