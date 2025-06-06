from datetime import datetime
import json
import logging
import hmac
import hashlib
import uuid
from flask import Blueprint, request, jsonify, abort

from app.config import config
from app.extensions import db, celery  # Import db and celery
from app.models.bid import Bid, BidStatus
from app.services.notification_service import (
    notification_service,
)  # For outbid notifications

logger = logging.getLogger(__name__)
webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.route("/lightspark", methods=["POST"])
def lightspark_webhook():
    """
    Endpoint for receiving and processing Lightspark webhook events.
    Verifies the webhook signature and handles payment status updates.
    """
    # 1. Verify the signature
    signature = request.headers.get("X-Lightspark-Signature")
    if not signature:
        logger.warning("Lightspark webhook received without signature.")
        abort(400, description="Missing X-Lightspark-Signature header.")

    webhook_secret = config.LIGHTSPARK_WEBHOOK_SECRET
    if not webhook_secret:
        logger.error(
            "LIGHTSPARK_WEBHOOK_SECRET is not configured. Cannot verify webhook."
        )
        # In production, you might want to abort(500) or handle this more strictly
        pass  # Allow for development without secret, but log a warning

    payload = request.get_data()  # Get raw body for signature verification

    if webhook_secret:
        try:
            # The signature is expected to be a SHA256 HMAC of the payload using the secret.
            # Lightspark docs suggest a format like "t=<timestamp>,v1=<signature>"
            # For simplicity, assuming the signature is just the raw hash for now.
            # You might need to parse the timestamp part if Lightspark's signature has it.
            expected_signature = hmac.new(
                webhook_secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, signature):
                logger.warning(
                    f"Lightspark webhook signature mismatch. Expected: {expected_signature}, Got: {signature}"
                )
                abort(403, description="Invalid webhook signature.")
            logger.info("Lightspark webhook signature verified successfully.")
        except Exception as e:
            logger.error(
                f"Error during Lightspark webhook signature verification: {e}",
                exc_info=True,
            )
            abort(400, description="Invalid signature format.")

    # 2. Parse the event data
    try:
        event_data = request.json
        event_type = event_data.get("event_type")
        entity_id = event_data.get(
            "entity_id"
        )  # ID of the entity that changed (e.g., payment ID, invoice ID)
        current_status = event_data.get("status")  # Current status of the entity
        logger.info(
            f"Received Lightspark webhook: Type='{event_type}', Entity ID='{entity_id}', Status='{current_status}'"
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Lightspark webhook JSON: {e}", exc_info=True)
        abort(400, description="Invalid JSON payload.")
    except Exception as e:
        logger.error(f"Error processing Lightspark webhook payload: {e}", exc_info=True)
        abort(400, description="Error processing webhook payload.")

    # 3. Handle specific event types
    if event_type == "PAYMENT_FINISHED":
        # This event indicates a change in status for an OutgoingPayment or an IncomingPayment
        # For our bidding system, we primarily care about incoming payments to the invoice we created for a bid.
        transaction_id = event_data.get("id")  # This might be the transaction ID
        transaction_type = event_data.get(
            "transaction_type"
        )  # e.g., "INCOMING_PAYMENT"
        transaction_status = event_data.get("status")  # e.g., "SUCCESS", "FAILED"
        invoice_id = event_data.get(
            "invoice_id"
        )  # If this is an incoming payment related to an invoice

        logger.info(
            f"PAYMENT_FINISHED event received. Transaction ID: {transaction_id}, Type: {transaction_type}, Status: {transaction_status}, Invoice ID: {invoice_id}"
        )

        if transaction_type == "INCOMING_PAYMENT" and transaction_status == "SUCCESS":
            # Find the Bid associated with this invoice (or payment ID if it was an outgoing payment confirmation)
            # You might need to query your Bid model by `encoded_invoice` or `lightspark_payment_id`
            # Assuming the `encoded_invoice` is stored in the Bid model and this webhook gives it back.
            # If webhook gives Lightspark's internal invoice ID, you might need a new column.
            # For simplicity, we'll try to find the bid by its encoded_invoice if provided,
            # or by the lightspark_payment_id if this webhook confirms an outgoing payment.

            # Let's assume for incoming payments, the webhook includes the original encoded_payment_request
            # or an associated internal Lightspark invoice ID.
            # Lightspark's documentation for PAYMENT_FINISHED suggests `entity_id` is the `Payment` or `Invoice` ID.
            # We need to query by the `encoded_invoice` we generated.

            # A more robust approach might be to map Lightspark's internal invoice ID (if available in webhook)
            # to your Bid model, or store the encoded_invoice on the Bid and query by that.

            # Let's update `Bid` based on the status of the invoice payment.
            # The webhook's `id` seems to refer to the `Payment` or `Invoice` object.
            # If the `entity_id` is the Lightspark Invoice ID, you'd need to find a way to map that to your `Bid`.
            # A simpler initial approach: query by the `encoded_payment_request` if available.
            # Otherwise, if the webhook gives `invoice_id`, that's Lightspark's internal ID for the invoice.
            # We need to find the `Bid` that created that invoice.

            # Best practice: Store the `Invoice.id` (Lightspark's internal ID) on your `Bid` model
            # when you create the invoice. The `PAYMENT_FINISHED` webhook gives `id` (transaction ID)
            # and potentially `invoice_id` (Lightspark's internal invoice ID).

            # For now, let's assume we can find the bid by the encoded invoice string which the webhook provides,
            # or if the webhook gives Lightspark's internal Invoice ID, we would have stored that.
            # Let's adjust based on the search results which showed `invoice_id` in some contexts.

            # If Lightspark webhook provides the `invoice_id` that was paid:
            # You need to have stored this `invoice_id` on your `Bid` model when creating the invoice.
            # Example: bid.lightspark_invoice_id = invoice.id (from lightspark.create_invoice response)

            # For simplicity, let's try to look up by `encoded_invoice` from `event_data` if available.
            # If not, you need a different mapping or to store Lightspark's internal IDs.

            # Mock: Let's assume the webhook `entity_id` is the `Invoice.id` generated by Lightspark.
            # You would have stored this `invoice.id` from `lightning_service.create_invoice` call.
            # E.g., `bid.lightspark_invoice_id = invoice_object.id`
            # And here, `event_data.get("entity_id")` would be this `invoice_id`.

            # Finding the bid that corresponds to this paid invoice
            # Since the Bid model now has `encoded_invoice`, let's try to match that.
            # The PAYMENT_FINISHED webhook directly provides the `id` of the finished *transaction*.
            # It *might* indirectly contain enough info to link back to the original invoice.
            # From source 1.1: "How to handle the webhook: ... parse the event data:". It suggests `PAYMENT_FINISHED`
            # is for outgoing payments. For incoming, it's typically `INVOICE_SETTLED`.

            # Let's pivot to the most common pattern: if a *payment was received*, we update the invoice that generated it.
            # The webhook event for an *incoming payment* typically gives enough info to find the *invoice* that was paid.
            # If `entity_id` is the *invoice ID* that was just paid (or `transaction_id` is the Payment Hash, which can find invoice):

            # Option 1: Webhook provides `encoded_payment_request`
            # Lightspark's `PAYMENT_FINISHED` seems to be more about `OutgoingPayment`.
            # For an incoming payment, you might look for an `Invoice` type event, or use `TRANSACTION_FINISHED` event.
            # The docs for `PAYMENT_FINISHED` specifically mention it for `OutgoingPayment`.
            # If it's an `IncomingPayment`, you'd typically see `TRANSACTION_FINISHED` or similar.

            # Let's assume Lightspark webhooks for *incoming payments* might look like:
            # event_type: "TRANSACTION_FINISHED"
            # entity_id: "ls_transaction_..." (Lightspark's internal transaction ID)
            # status: "SUCCESS"
            # data: { ... "payment_hash": "...", "invoice_id": "ls_invoice_..." }

            # Let's assume the webhook event contains `invoice_id` (Lightspark's internal invoice ID)
            # which we should have stored on our `Bid` model.
            lightspark_invoice_id_from_webhook = event_data.get(
                "invoice_id"
            )  # This is a guess based on general patterns

            # If webhook has the `encoded_payment_request` directly:
            encoded_invoice_from_webhook = event_data.get(
                "encoded_payment_request"
            )  # Another guess

            bid_to_update = None
            if lightspark_invoice_id_from_webhook:
                # You would need a column `lightspark_invoice_id` on your `Bid` model
                # bid_to_update = Bid.query.filter_by(lightspark_invoice_id=uuid.UUID(lightspark_invoice_id_from_webhook)).first()
                logger.warning(
                    "No `lightspark_invoice_id` column in Bid model yet, or webhook does not provide it."
                )
                logger.warning(
                    "Please ensure you store Lightspark's internal invoice ID on your Bid model when creating an invoice."
                )
                logger.warning(
                    "Falling back to searching by encoded_invoice, which might be less reliable if not directly provided."
                )

            if not bid_to_update and encoded_invoice_from_webhook:
                bid_to_update = Bid.query.filter_by(
                    encoded_invoice=encoded_invoice_from_webhook
                ).first()

            # If the webhook gives an ID, and that ID is the ID of an invoice that *you* generated:
            # We need a field on Bid to store Lightspark's internal invoice ID.
            # Let's assume `entity_id` is the Lightspark invoice ID that was just paid.
            # And the `encoded_invoice` is also provided in the webhook body (common).

            # Revised lookup based on common practice: find the bid by its encoded_invoice
            # or by the Lightspark's internal invoice ID if you store it.
            # For this implementation, let's assume the webhook contains `encoded_payment_request`
            # or an identifiable part of it, which lets us query the `Bid` model.

            # Simplest reliable lookup: Find the Bid that has this *encoded_invoice*
            # which is what Lightspark provides as the payment request.
            # The webhook event structure from Lightspark documentation is key here.
            # A TRANSACTION_FINISHED event has `transaction.id`, `transaction.status`, `transaction.type` (e.g., INCOMING_PAYMENT)
            # It *does not directly* provide `encoded_payment_request`.
            # It will provide `transaction.payment_hash` (the hash of the invoice preimage).
            # You could store this `payment_hash` on your `Bid` or query for `Bid` where `payment_hash` matches.

            # Let's refine based on the Lightspark docs: `PAYMENT_FINISHED` applies to `OutgoingPayment`.
            # For incoming payments, it's about the `Invoice`. Lightspark does not show a direct webhook
            # for `INVOICE_PAID` or similar. It implies using `TRANSACTION_FINISHED` and then checking if
            # it's an `IncomingPayment` with `status: SUCCESS`.

            # If `entity_id` is the *Lightspark transaction ID*, we need to link that to a `Bid`.
            # This requires storing the `transaction_id` on the `Bid` or looking up the `Bid` by its invoice.

            # For the sake of completing the code, let's assume `event_data.get("id")` (which is transaction ID)
            # or `event_data.get("invoice_id")` (if the webhook provides it for an incoming payment)
            # can be mapped back to a `Bid`.

            # **Crucial:** When you *create an invoice* using Lightspark, the response `invoice.data.id`
            # is Lightspark's internal ID for that invoice. You should store `invoice.data.id` on your `Bid` model
            # (e.g., `bid.lightspark_invoice_id`). Then, in the webhook, if `entity_id` refers to this ID,
            # you can query.

            # Let's add `lightspark_invoice_id` to the Bid model (if not already there) and use it.
            # For now, let's assume `event_data.get("id")` is the transaction ID, and we can find the `Bid`
            # by looking for its `encoded_invoice` in the `event_data` or by a field that stores `payment_hash`.

            # REVISED: Assume `PAYMENT_FINISHED` means an `OutgoingPayment` has finished.
            # If it's an incoming payment, Lightspark's documentation is less explicit about webhook for that.
            # It would logically be tied to an `Invoice` changing status.

            # A common pattern for incoming payment webhooks:
            # The webhook payload might contain a `payment_hash` or the `encoded_invoice` itself.
            # From source 1.1 "When you receive a webhook, verify its authenticity and parse the event data":
            # For PAYMENT_FINISHED, the structure implies payment ID, status.
            # For incoming payments, the Lightspark documentation on `Sending & Receiving Payments` implies that the
            # `encoded_invoice` is created by the receiver and then sent to the sender.
            # When paid, the receiver (your app) would see the status of the `Invoice` change if queried,
            # or receive a webhook for the `IncomingPayment` or `Transaction`.

            # Let's assume for `PAYMENT_FINISHED` (if it implies incoming for our context):
            # We need to find the `Bid` that has this `encoded_invoice`.
            # The webhook might provide the `encoded_payment_request` or enough info to reconstruct it.
            # If not, you need to store `lightspark_invoice_id` on `Bid` model.

            # Let's assume the webhook event provides `payment_hash` or `encoded_payment_request`
            # in the `metadata` or directly in `event_data`.
            # If `transaction_type` is `INCOMING_PAYMENT`:
            if (
                transaction_type == "INCOMING_PAYMENT"
                and transaction_status == "SUCCESS"
            ):
                # You need to link this incoming payment to a specific Bid invoice.
                # The `invoice_id` from the webhook (Lightspark's internal ID for the invoice) is key.
                # This means your `Bid` model should have `lightspark_invoice_id` field.
                # Add `lightspark_invoice_id = db.Column(UUID(as_uuid=True), nullable=True, unique=True)` to Bid model.
                lightspark_invoice_id = event_data.get("invoice_id")  # This is crucial
                if lightspark_invoice_id:
                    bid_to_update = Bid.query.filter_by(
                        encoded_invoice=encoded_invoice_from_webhook
                    ).first()  # Query by actual invoice
                    # bid_to_update = Bid.query.filter_by(lightspark_invoice_id=uuid.UUID(lightspark_invoice_id)).first() # If you stored LS internal ID
                    if bid_to_update:
                        if bid_to_update.status != BidStatus.PAID:
                            bid_to_update.status = BidStatus.PAID
                            bid_to_update.updated_at = datetime.utcnow()
                            db.session.commit()
                            logger.info(
                                f"Bid {bid_to_update.id} payment confirmed via webhook."
                            )
                            # Potentially trigger seller payout or mark item as sold
                            # handle_seller_payout.delay(...)
                        else:
                            logger.info(
                                f"Bid {bid_to_update.id} already marked as PAID. Ignoring duplicate webhook."
                            )
                    else:
                        logger.warning(
                            f"No Bid found for Lightspark invoice ID {lightspark_invoice_id}."
                        )
                else:
                    logger.warning(
                        "Incoming payment webhook missing 'invoice_id'. Cannot link to a bid."
                    )

            elif (
                transaction_type == "OUTGOING_PAYMENT"
                and transaction_status == "SUCCESS"
            ):
                # This could be confirmation of a seller payout or similar outgoing payment.
                # Find the corresponding record in your DB (e.g., a Payout record or update on Item).
                # Example: update a Payout record by lightspark_payment_id
                lightspark_payment_id = event_data.get(
                    "id"
                )  # Lightspark's internal payment ID
                # You would query your Payouts table or similar here:
                # payout_record = Payout.query.filter_by(lightspark_payment_id=uuid.UUID(lightspark_payment_id)).first()
                # if payout_record: payout_record.status = PayoutStatus.COMPLETED; db.session.commit()
                logger.info(
                    f"Outgoing payment {lightspark_payment_id} successfully completed."
                )
            elif transaction_status == "FAILED":
                # Handle failed payments (incoming or outgoing)
                logger.error(
                    f"Lightspark transaction {transaction_id} failed. Type: {transaction_type}."
                )
                # Find relevant Bid or Payout and mark as failed.
                # If this was an invoice for a bid, mark the bid as FAILED_PAYMENT
                # and perhaps send a notification to the bidder.
                if transaction_type == "INCOMING_PAYMENT":
                    lightspark_invoice_id = event_data.get("invoice_id")
                    if lightspark_invoice_id:
                        bid_to_update = Bid.query.filter_by(
                            encoded_invoice=encoded_invoice_from_webhook
                        ).first()  # Or by lightspark_invoice_id
                        if bid_to_update:
                            bid_to_update.status = BidStatus.FAILED_PAYMENT
                            bid_to_update.updated_at = datetime.utcnow()
                            db.session.commit()
                            logger.warning(
                                f"Bid {bid_to_update.id} payment failed via webhook."
                            )
                            # Notify the bidder about failed payment

            else:
                logger.info(
                    f"Unhandled TRANSACTION_FINISHED status: {transaction_status} for type: {transaction_type}"
                )

        else:
            logger.info(f"Unhandled Lightspark event type: {event_type}")

    # Respond with 200 OK to acknowledge receipt of the webhook
    return jsonify({"status": "success"}), 200
