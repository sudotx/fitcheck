from cryptography.fernet import Fernet
from app.config import config
import base64
import os


# Generate a key if not exists
def get_encryption_key():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        key = Fernet.generate_key()
        # Store this key securely in your environment variables
        print(
            "WARNING: Generated new encryption key. Please set ENCRYPTION_KEY in your environment variables."
        )
    return key


# Initialize Fernet cipher
cipher_suite = Fernet(get_encryption_key())


def encrypt_data(data):
    """Encrypt sensitive data"""
    if data is None:
        return None
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data):
    """Decrypt sensitive data"""
    if encrypted_data is None:
        return None
    return cipher_suite.decrypt(encrypted_data.encode()).decode()
