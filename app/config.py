import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 mins
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    INSTAGRAM_APP_ID = ""
    INSTAGRAM_APP_SECRET = ""
    REDIRECT_URI = ""
