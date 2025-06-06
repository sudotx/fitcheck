import os
import lightspark
import logging
from typing import Optional, Dict, Any
import uuid

from app.config import config  # Assuming config is imported from your app's config

logger = logging.getLogger(__name__)


class LightningService:
    """
    Service for interacting with the Lightspark API for Lightning Network operations.
    """

    def __init__(self):
        """
        Initializes the Lightspark client.
        Ensures API credentials and Node ID are loaded from configuration.
        """
        self._client: Optional[lightspark.LightsparkSyncClient] = None
        self.api_token_id = config.LIGHTSPARK_API_TOKEN_CLIENT_ID
        self.api_token_secret = config.LIGHTSPARK_API_TOKEN_CLIENT_SECRET
        self.node_id = config.LIGHTSPARK_NODE_ID

        if not self.api_token_id or not self.api_token_secret or not self.node_id:
            logger.error(
                "Lightspark API credentials or Node ID are not configured. Check LIGHTSPARK_API_TOKEN_CLIENT_ID, LIGHTSPARK_API_TOKEN_CLIENT_SECRET, and LIGHTSPARK_NODE_ID environment variables."
            )
        else:
            self._client = lightspark.LightsparkSyncClient(
                api_token_client_id=self.api_token_id,
                api_token_client_secret=self.api_token_secret,
            )
            logger.info("LightsparkSyncClient initialized.")

    @property
    def client(self) -> lightspark.LightsparkSyncClient:
        """
        Returns the Lightspark client instance, raising an error if not initialized.
        """
        if not self._client:
            raise RuntimeError(
                "LightsparkService not initialized. Missing API credentials or Node ID."
            )
        return self._client

    def create_invoice(
        self, amount_sats: float, memo: str, expiry_secs: int = 3600
    ) -> Optional[str]:
        """
        Creates a new Lightning invoice (BOLT11) using Lightspark.

        Args:
            amount_sats (float): The amount of the invoice in Satoshis.
            memo (str): A description for the invoice.
            expiry_secs (int): The invoice expiration time in seconds (default: 1 hour).

        Returns:
            Optional[str]: The encoded BOLT11 invoice string if successful, None otherwise.
        """
        try:
            # Lightspark amounts are in millisatoshis (msats)
            amount_msats = int(amount_sats * 1000)
            logger.info(
                f"Creating invoice for {amount_sats} sats ({amount_msats} msats) with memo: '{memo}' for node: {self.node_id}"
            )

            invoice = self.client.create_invoice(
                node_id=self.node_id,
                amount_msats=amount_msats,
                memo=memo,
                expiry_secs=expiry_secs,
            )
            if invoice and invoice.data and invoice.data.encoded_payment_request:
                encoded_invoice = invoice.data.encoded_payment_request
                logger.info(f"Successfully created invoice: {encoded_invoice}")
                return encoded_invoice
            else:
                logger.error(f"Failed to create invoice. Response: {invoice}")
                return None
        except Exception as e:
            logger.error(f"Error creating Lightspark invoice: {e}", exc_info=True)
            return None

    def pay_invoice(
        self,
        encoded_invoice: str,
        maximum_fees_sats: Optional[float] = None,
        timeout_secs: int = 60,
    ) -> Optional[lightspark.OutgoingPayment]:
        """
        Pays a Lightning invoice using Lightspark.

        Args:
            encoded_invoice (str): The BOLT11 invoice string to pay.
            maximum_fees_sats (Optional[float]): Maximum fees to pay in Satoshis. Defaults to 500 sats.
            timeout_secs (int): Timeout for the payment in seconds.

        Returns:
            Optional[lightspark.OutgoingPayment]: The OutgoingPayment object if successful, None otherwise.
        """
        try:
            # Convert maximum_fees_sats to millisatoshis if provided
            maximum_fees_msats = (
                int(maximum_fees_sats * 1000)
                if maximum_fees_sats is not None
                else 500000
            )  # 500 sats default

            logger.info(
                f"Attempting to pay invoice {encoded_invoice} from node {self.node_id} with max fees: {maximum_fees_sats} sats"
            )

            # Note: For sensitive operations like paying, Lightspark recommends unlocking the node.
            # This SDK uses `LightsparkSyncClient`, which handles internal signing if configured.
            # If you encounter issues, ensure your Lightspark account/node has the necessary
            # permissions and key management setup (e.g., Remote Signing).
            payment = self.client.pay_invoice(
                node_id=self.node_id,
                encoded_invoice=encoded_invoice,
                timeout_secs=timeout_secs,
                maximum_fees_msats=maximum_fees_msats,
            )

            if payment:
                logger.info(
                    f"Payment initiated. ID: {payment.id}, Status: {payment.status}"
                )
                return payment
            else:
                logger.error(
                    f"Failed to initiate payment for invoice: {encoded_invoice}. Response: {payment}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error paying Lightspark invoice {encoded_invoice}: {e}", exc_info=True
            )
            return None

    def get_payment_status(
        self, payment_id: str
    ) -> Optional[lightspark.TransactionStatus]:
        """
        Retrieves the status of an outgoing Lightning payment.

        Args:
            payment_id (str): The ID of the outgoing payment.

        Returns:
            Optional[lightspark.TransactionStatus]: The status of the payment, or None if not found.
        """
        try:
            # The get_entity method requires the object type to retrieve.
            payment = self.client.get_entity(payment_id, lightspark.OutgoingPayment)
            if payment:
                logger.info(f"Payment {payment_id} status: {payment.status}")
                return payment.status
            else:
                logger.warning(f"Payment {payment_id} not found.")
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving payment status for {payment_id}: {e}", exc_info=True
            )
            return None


# Create a singleton instance of the LightningService
lightning_service = LightningService()
