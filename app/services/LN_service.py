import logging
from typing import Optional, Dict, Any
import uuid

from app.config import PaymentConfig
from .payment_factory import PaymentServiceFactory

logger = logging.getLogger(__name__)


class LightningService:
    """
    Service for interacting with Lightning Network operations.
    Now uses the payment provider abstraction.
    """

    def __init__(self):
        """Initialize the payment service"""
        self._payment_service = PaymentServiceFactory.get_payment_service()
        logger.info("LightningService initialized with payment provider")

    def create_invoice(
        self,
        amount_sats: float,
        customer_email: str,
        description: str = "Payment for FitCheck",
        expires_at: str = "24h",
        private: bool = False,
        is_including_private_channels: bool = False,
        is_fallback_included: bool = True,
    ) -> Optional[str]:
        """
        Creates a new Lightning invoice using the configured payment provider.

        Args:
            amount_sats (float): The amount of the invoice in Satoshis.
            customer_email (str): Email of the customer making the payment.
            description (str): A description for the invoice.
            expires_at (str): The invoice expiration time (default: "24h").
            private (bool): Whether the invoice is private.
            is_including_private_channels (bool): Whether to include private channels.
            is_fallback_included (bool): Whether to include fallback address.

        Returns:
            Optional[str]: The encoded BOLT11 invoice string if successful, None otherwise.
        """
        try:
            response = self._payment_service.create_invoice(
                amount_sats=amount_sats,
                customer_email=customer_email,
                description=description,
                expires_at=expires_at,
                private=private,
                is_including_private_channels=is_including_private_channels,
                is_fallback_included=is_fallback_included,
            )

            if response:
                return response.encoded_invoice
            return None

        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return None

    def pay_invoice(
        self,
        encoded_invoice: str,
        customer_email: str,
        reference: str = None,
        description: str = "Payment from FitCheck",
    ) -> Optional[Dict[str, Any]]:
        """
        Pays a Lightning invoice using the configured payment provider.

        Args:
            encoded_invoice (str): The BOLT11 invoice string to pay.
            customer_email (str): Email of the customer making the payment.
            reference (str): Optional reference for the payment.
            description (str): Description of the payment.

        Returns:
            Optional[Dict[str, Any]]: The payment response if successful, None otherwise.
        """
        try:
            if not reference:
                reference = f"fitcheck-payment-{uuid.uuid4()}"

            response = self._payment_service.pay_invoice(
                encoded_invoice=encoded_invoice,
                customer_email=customer_email,
                reference=reference,
                description=description,
            )

            if response:
                return response.raw_response
            return None

        except Exception as e:
            logger.error(f"Error paying invoice: {e}", exc_info=True)
            return None

    def get_invoice_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the status of a Lightning invoice.

        Args:
            invoice_id (str): The ID of the invoice.

        Returns:
            Optional[Dict[str, Any]]: The invoice status and details if found, None otherwise.
        """
        try:
            return self._payment_service.get_invoice_status(invoice_id)
        except Exception as e:
            logger.error(f"Error retrieving invoice status: {e}", exc_info=True)
            return None


# Create a singleton instance of the LightningService
lightning_service = LightningService()
