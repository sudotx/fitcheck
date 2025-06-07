import os
from bitnob import Lightning
import logging
from typing import Optional, Dict, Any
import uuid

from app.config import config

logger = logging.getLogger(__name__)


class LightningService:
    """
    Service for interacting with the Bitnob API for Lightning Network operations.
    """

    def __init__(self):
        """
        Initializes the Bitnob Lightning client.
        Ensures API key is loaded from configuration.
        """
        self.api_key = config.BITNOB_API_KEY
        self.is_production = config.BITNOB_PRODUCTION

        if not self.api_key:
            logger.error(
                "Bitnob API key is not configured. Check BITNOB_API_KEY environment variable."
            )
        else:
            # Set environment variables for Bitnob
            os.environ["BITNOB_API_KEY"] = self.api_key
            os.environ["BITNOB_PRODUCTION"] = str(self.is_production).lower()

            self._client = Lightning()
            logger.info("Bitnob Lightning client initialized.")

    @property
    def client(self) -> Lightning:
        """
        Returns the Bitnob Lightning client instance, raising an error if not initialized.
        """
        if not self._client:
            raise RuntimeError("LightningService not initialized. Missing API key.")
        return self._client

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
        Creates a new Lightning invoice (BOLT11) using Bitnob.

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
            logger.info(
                f"Creating invoice for {amount_sats} sats with description: '{description}' for customer: {customer_email}"
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

            response = self.client.create_invoice(payload)

            if response and response.get("data"):
                invoice_data = response["data"]
                logger.info(f"Successfully created invoice: {invoice_data}")
                return invoice_data
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
    ) -> Optional[Dict[str, Any]]:
        """
        Pays a Lightning invoice using Bitnob.

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

            logger.info(
                f"Attempting to pay invoice {encoded_invoice} for customer {customer_email}"
            )

            payload = {
                "customerEmail": customer_email,
                "reference": reference,
                "description": description,
                "payment_request": encoded_invoice,
            }

            response = self.client.pay_invoice(payload)

            if response and response.get("data"):
                logger.info(
                    f"Payment initiated. Reference: {reference}, Response: {response}"
                )
                return response
            else:
                logger.error(
                    f"Failed to initiate payment for invoice: {encoded_invoice}. Response: {response}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error paying Bitnob invoice {encoded_invoice}: {e}", exc_info=True
            )
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
            response = self.client.get_invoice(invoice_id)
            if response and response.get("data"):
                logger.info(f"Invoice {invoice_id} status: {response['data']}")
                return response["data"]
            else:
                logger.warning(f"Invoice {invoice_id} not found.")
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving invoice status for {invoice_id}: {e}", exc_info=True
            )
            return None


# Create a singleton instance of the LightningService
lightning_service = LightningService()
