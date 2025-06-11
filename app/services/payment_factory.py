from typing import Optional
from .payment_service import PaymentService, PaymentProviderType
from app.config import PaymentConfig


class PaymentServiceFactory:
    """Factory for creating payment service instances"""

    _instance: Optional[PaymentService] = None

    @classmethod
    def get_payment_service(cls) -> PaymentService:
        """
        Get or create a payment service instance with the configured provider

        Returns:
            PaymentService: Configured payment service instance
        """
        if cls._instance is None:
            provider_type = PaymentProviderType(PaymentConfig.DEFAULT_PROVIDER)

            # Configure provider-specific settings
            provider_config = {}
            if provider_type == PaymentProviderType.BITNOB:
                provider_config = {
                    "api_key": PaymentConfig.BITNOB_API_KEY,
                    "is_production": PaymentConfig.BITNOB_PRODUCTION,
                }
            # Add more provider configurations here
            # elif provider_type == PaymentProviderType.LIGHTSPARK:
            #     provider_config = {
            #         "api_key": PaymentConfig.LIGHTSPARK_API_KEY
            #     }

            cls._instance = PaymentService(provider_type, **provider_config)

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the payment service instance (useful for testing)"""
        cls._instance = None
