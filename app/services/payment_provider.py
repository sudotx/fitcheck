from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InvoiceResponse:
    """Standardized response for invoice creation"""

    invoice_id: str
    encoded_invoice: str
    amount_sats: float
    expires_at: str
    status: str
    raw_response: Dict[str, Any]


@dataclass
class PaymentResponse:
    """Standardized response for payment operations"""

    payment_id: str
    status: str
    amount_sats: float
    reference: str
    raw_response: Dict[str, Any]


class PaymentProvider(ABC):
    """Abstract base class for payment providers"""

    @abstractmethod
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
        pass

    @abstractmethod
    def pay_invoice(
        self,
        encoded_invoice: str,
        customer_email: str,
        reference: str = None,
        description: str = "Payment from FitCheck",
    ) -> Optional[PaymentResponse]:
        """Pay an existing invoice"""
        pass

    @abstractmethod
    def get_invoice_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an invoice"""
        pass


class BitnobPaymentProvider(PaymentProvider):
    """Bitnob implementation of the PaymentProvider interface"""

    def __init__(self, api_key: str, is_production: bool = False):
        from bitnob import Lightning
        import os

        self.api_key = api_key
        self.is_production = is_production

        if not self.api_key:
            logger.error("Bitnob API key is not configured")
            raise ValueError("Bitnob API key is required")

        # Set environment variables for Bitnob
        os.environ["BITNOB_API_KEY"] = self.api_key
        os.environ["BITNOB_PRODUCTION"] = str(self.is_production).lower()

        self._client = Lightning()
        logger.info("Bitnob Lightning client initialized")

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
        try:
            logger.info(
                f"Creating invoice for {amount_sats} sats for customer: {customer_email}"
            )

            payload = {
                "customerEmail": customer_email,
                "description": description,
                "tokens": amount_sats,
                "expires_at": expires_at,
                "private": private,
                "is_including_private_channels": is_including_private_channels,
                "is_fallback_included": is_fallback_included,
            }

            response = self._client.create_invoice(payload)

            if response and response.get("data"):
                invoice_data = response["data"]
                logger.info(f"Successfully created invoice: {invoice_data}")

                return InvoiceResponse(
                    invoice_id=invoice_data.get("id"),
                    encoded_invoice=invoice_data.get("payment_request"),
                    amount_sats=float(invoice_data.get("tokens", 0)),
                    expires_at=invoice_data.get("expires_at"),
                    status=invoice_data.get("status"),
                    raw_response=invoice_data,
                )
            else:
                logger.error(f"Failed to create invoice. Response: {response}")
                return None

        except Exception as e:
            logger.error(f"Error creating Bitnob invoice: {e}", exc_info=True)
            return None

    def pay_invoice(
        self,
        encoded_invoice: str,
        customer_email: str,
        reference: str = None,
        description: str = "Payment from FitCheck",
    ) -> Optional[PaymentResponse]:
        try:
            if not reference:
                reference = f"fitcheck-payment-{uuid.uuid4()}"

            logger.info(f"Attempting to pay invoice for customer {customer_email}")

            payload = {
                "customerEmail": customer_email,
                "reference": reference,
                "description": description,
                "payment_request": encoded_invoice,
            }

            response = self._client.pay_invoice(payload)

            if response and response.get("data"):
                payment_data = response["data"]
                logger.info(f"Payment initiated. Reference: {reference}")

                return PaymentResponse(
                    payment_id=payment_data.get("id"),
                    status=payment_data.get("status"),
                    amount_sats=float(payment_data.get("amount", 0)),
                    reference=reference,
                    raw_response=payment_data,
                )
            else:
                logger.error(f"Failed to initiate payment. Response: {response}")
                return None

        except Exception as e:
            logger.error(f"Error paying Bitnob invoice: {e}", exc_info=True)
            return None

    def get_invoice_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self._client.get_invoice(invoice_id)
            if response and response.get("data"):
                logger.info(f"Invoice {invoice_id} status: {response['data']}")
                return response["data"]
            else:
                logger.warning(f"Invoice {invoice_id} not found.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving invoice status: {e}", exc_info=True)
            return None
