import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")
    APP_NAME = "FitCheck"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MongoDB Privacy Vault
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB = os.getenv("MONGODB_DB", "privacy_vault")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

    # Add these MongoDB specific settings
    MONGODB_SETTINGS = {
        "ssl": True,
        "ssl_cert_reqs": "CERT_NONE",  # For development only
        "tlsAllowInvalidCertificates": True,  # For development only
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 20000,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days

    # Storage
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET")

    # Google Cloud
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    # AI
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Search
    ALGOLIA_APP_ID = os.getenv("ALGOLIA_APP_ID")
    ALGOLIA_API_KEY = os.getenv("ALGOLIA_WRITE_API_KEY")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # AWS S3
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

    # Redis & Celery
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Google AI
    GEMINI_MODEL = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL = "models/embedding-001"

    # AI Models
    CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
    EMBEDDING_DIMENSION = 512

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Sentry
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # Firebase/OneSignal
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
    ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
    ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")

    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Security
    PASSWORD_SALT = os.getenv("PASSWORD_SALT")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")

    # Bitnob API Credentials
    BITNOB_API_KEY = os.environ.get("BITNOB_API_KEY")
    BITNOB_PRODUCTION = False


class ProductionConfig(Config):
    MONGODB_SETTINGS = {
        "ssl": True,
        "ssl_cert_reqs": "CERT_REQUIRED",
        "tlsAllowInvalidCertificates": False,
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 20000,
    }


class PaymentConfig:
    """Payment provider configuration"""

    DEFAULT_PROVIDER = "bitnob"  # Can be overridden in environment

    # Bitnob configuration
    BITNOB_API_KEY = os.getenv("BITNOB_API_KEY")
    BITNOB_PRODUCTION = os.getenv("BITNOB_PRODUCTION", "false").lower() == "true"

    # Add more provider configurations here
    # LIGHTSPARK_API_KEY = os.getenv("LIGHTSPARK_API_KEY")
    # STRIKE_API_KEY = os.getenv("STRIKE_API_KEY")


config = Config()
