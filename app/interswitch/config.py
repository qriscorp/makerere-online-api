"""Interswitch configuration loaded from environment or system settings."""
import os


# Interswitch API configuration
INTERSWITCH_URL = os.getenv("INTERSWITCH_URL", "https://dev.interswitch.io")
INTERSWITCH_CLIENT_ID = os.getenv("INTERSWITCH_CLIENT_ID", "")
INTERSWITCH_CLIENT_SECRET = os.getenv("INTERSWITCH_CLIENT_SECRET", "")
INTERSWITCH_MERCHANT_CODE = os.getenv("INTERSWITCH_MERCHANT_CODE", "")
INTERSWITCH_PAYABLE_CODE = os.getenv("INTERSWITCH_PAYABLE_CODE", "")
INTERSWITCH_TERMINAL_ID = os.getenv("INTERSWITCH_TERMINAL_ID", "3ISO9881")
INTERSWITCH_SERIAL_ID = os.getenv("INTERSWITCH_SERIAL_ID", "038732999900466")
INTERSWITCH_PASSWORD = os.getenv("INTERSWITCH_PASSWORD", "")

# Billers API
INTERSWITCH_BILLERS_API_URL = os.getenv(
    "INTERSWITCH_BILLERS_API_URL",
    "https://iswapigateway-develop.azurewebsites.net/"
)

# Mobile Money payment codes (configured by admin in system settings or env)
MTN_PAYMENT_CODE = os.getenv("MTN_PAYMENT_CODE", "")
AIRTEL_PAYMENT_CODE = os.getenv("AIRTEL_PAYMENT_CODE", "")

# Phone prefixes for carrier detection (Uganda)
MTN_PREFIXES = ("077", "078", "076", "079")
AIRTEL_PREFIXES = ("075", "074", "070")


def detect_carrier(phone: str) -> str:
    """Detect mobile carrier from phone number prefix."""
    normalized = normalize_phone(phone)
    if normalized[:3] in MTN_PREFIXES:
        return "mtn"
    elif normalized[:3] in AIRTEL_PREFIXES:
        return "airtel"
    return "unknown"


def normalize_phone(phone: str) -> str:
    """Normalize phone number to local format (0XXXXXXXXX)."""
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("256"):
        p = "0" + p[3:]
    if len(p) == 9 and p.isdigit() and p.startswith("7"):
        p = "0" + p
    return p
