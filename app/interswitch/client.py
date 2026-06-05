"""
Interswitch API client — handles authentication, signatures, and payment requests.
Simplified from the kumpi implementation for the university payment context.
"""
import hashlib
import hmac
import time
import uuid
import httpx
import logging

from app.interswitch.config import (
    INTERSWITCH_URL,
    INTERSWITCH_CLIENT_ID,
    INTERSWITCH_CLIENT_SECRET,
    INTERSWITCH_TERMINAL_ID,
    INTERSWITCH_SERIAL_ID,
    INTERSWITCH_PASSWORD,
    INTERSWITCH_BILLERS_API_URL,
)

logger = logging.getLogger(__name__)


def generate_request_reference(prefix: str = "mak-") -> str:
    """Generate unique request reference."""
    return f"{prefix}{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"


def _create_signature(http_method: str, resource_url: str, timestamp: str) -> str:
    """Create InterswitchAuth signature (HMAC-SHA256)."""
    signature_string = f"{http_method}&{resource_url}&{timestamp}"
    signature = hmac.new(
        INTERSWITCH_CLIENT_SECRET.encode(),
        signature_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return signature


def _get_headers(method: str, url: str) -> dict:
    """Generate Interswitch API headers with authentication."""
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex

    headers = {
        "Content-Type": "application/json",
        "Timestamp": timestamp,
        "Nonce": nonce,
        "TerminalId": INTERSWITCH_TERMINAL_ID,
    }

    if INTERSWITCH_CLIENT_ID:
        headers["ClientId"] = INTERSWITCH_CLIENT_ID

    return headers


async def make_payment_request(
    payment_code: str,
    customer_id: str,
    amount: str,
    request_reference: str = None,
) -> dict:
    """
    Make an express payment request to Interswitch.
    This is used for mobile money collections (course fee payments).

    Args:
        payment_code: The biller payment code (MTN or Airtel)
        customer_id: The phone number to charge
        amount: Amount in UGX (string)
        request_reference: Unique transaction reference

    Returns:
        Interswitch API response dict
    """
    if not request_reference:
        request_reference = generate_request_reference()

    endpoint = f"{INTERSWITCH_URL}/api/v1/phoenix/sente/expressPayment"

    payload = {
        "paymentCode": payment_code,
        "customerId": customer_id,
        "amount": amount,
        "requestReference": request_reference,
        "terminalId": INTERSWITCH_TERMINAL_ID,
    }

    headers = _get_headers("POST", endpoint)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            result = response.json()
            logger.info(f"Interswitch payment response: {result}")
            return result
    except Exception as e:
        logger.error(f"Interswitch payment error: {e}")
        return {
            "responseCode": "99999",
            "responseMessage": f"Connection error: {str(e)}",
        }


async def validate_customer(
    payment_code: str,
    customer_id: str,
    amount: str,
) -> dict:
    """Validate customer before payment."""
    request_reference = generate_request_reference(prefix="val-")

    endpoint = f"{INTERSWITCH_URL}/api/v1/phoenix/sente/customerValidation"

    payload = {
        "paymentCode": payment_code,
        "customerId": customer_id,
        "amount": amount,
        "requestReference": request_reference,
        "terminalId": INTERSWITCH_TERMINAL_ID,
    }

    headers = _get_headers("POST", endpoint)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            return response.json()
    except Exception as e:
        logger.error(f"Interswitch validation error: {e}")
        return {
            "responseCode": "99999",
            "responseMessage": f"Connection error: {str(e)}",
        }


def is_payment_successful(response: dict) -> bool:
    """Check if an Interswitch response indicates success."""
    response_code = response.get("responseCode", "")
    response_message = response.get("responseMessage", "")

    if response_code != "90000":
        return False

    # Check for error indicators in message
    error_indicators = [
        "API Error", "HTTPSConnectionPool", "Max retries",
        "Failed to resolve", "Connection refused", "Timeout",
    ]
    for indicator in error_indicators:
        if indicator.lower() in response_message.lower():
            return False

    return True
