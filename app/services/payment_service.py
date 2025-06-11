from typing import Optional, Dict, Any
import logging
from enum import Enum
from .payment_provider import PaymentProvider, InvoiceResponse, PaymentResponse

logger = logging.getLogger(__name__)


class PaymentProviderType(Enum):
    BITNOB = "bitnob"
    # Add more providers here as needed
    # LIGHTSPARK = "lightspark"
    # STRIKE = "strike"


class PaymentService:
    """Main payment service that manages different payment providers"""

    def __init__(self, provider_type: PaymentProviderType, **provider_config):
        """
        Initialize the payment service with a specific provider

        Args:
            provider_type: The type of payment provider to use
            provider_config: Configuration specific to the provider
        """
        self.provider = self._create_provider(provider_type, **provider_config)

    def _create_provider(
        self, provider_type: PaymentProviderType, **config
    ) -> PaymentProvider:
        """Create a payment provider instance based on the type"""
        if provider_type == PaymentProviderType.BITNOB:
            from .payment_provider import BitnobPaymentProvider

            return BitnobPaymentProvider(
                api_key=config.get("api_key"),
                is_production=config.get("is_production", False),
            )
        # Add more provider implementations here
        # elif provider_type == PaymentProviderType.LIGHTSPARK:
        #     from .payment_provider import LightsparkPaymentProvider
        #     return LightsparkPaymentProvider(**config)
        else:
            raise ValueError(f"Unsupported payment provider: {provider_type}")

    def create_invoice(
        self,
        amount_sats: float,
        customer_email: str,
        description: str = "Payment for FitCheck",
        expires_at: str = "24h",
        private: bool = False,
        is_including_private_channels: bool = False,
        is_fallback_included: bool = True,
    ) -> Optional[InvoiceResponse]:
        """Create a new payment invoice"""
        return self.provider.create_invoice(
            amount_sats=amount_sats,
            customer_email=customer_email,
            description=description,
            expires_at=expires_at,
            private=private,
            is_including_private_channels=is_including_private_channels,
            is_fallback_included=is_fallback_included,
        )

    def pay_invoice(
        self,
        encoded_invoice: str,
        customer_email: str,
        reference: str = None,
        description: str = "Payment from FitCheck",
    ) -> Optional[PaymentResponse]:
        """Pay an existing invoice"""
        return self.provider.pay_invoice(
            encoded_invoice=encoded_invoice,
            customer_email=customer_email,
            reference=reference,
            description=description,
        )

    def get_invoice_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an invoice"""
        return self.provider.get_invoice_status(invoice_id)
