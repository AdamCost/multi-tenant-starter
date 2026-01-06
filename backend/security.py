"""
Security utilities for the application
"""
import re
import bleach


# PII patterns to scrub before sending to external APIs
PII_PATTERNS = [
    # Email addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # Phone numbers (various formats)
    (r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', '[PHONE]'),
    # SSN
    (r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b', '[SSN]'),
    # Credit card numbers (basic pattern)
    (r'\b(?:\d{4}[-.\s]?){3}\d{4}\b', '[CARD]'),
    # IP addresses
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
]

# Compile patterns for performance
_COMPILED_PII_PATTERNS = [(re.compile(p, re.IGNORECASE), r) for p, r in PII_PATTERNS]


def scrub_pii(text: str) -> str:
    """
    Remove personally identifiable information from text before sending to external APIs.

    Scrubs: emails, phone numbers, SSNs, credit cards, IP addresses.
    This protects participant privacy when data is processed by third-party AI services.
    """
    if not text:
        return ""

    result = text
    for pattern, replacement in _COMPILED_PII_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


def sanitize_chat_message(message: str) -> str:
    """
    Sanitize user input for chat messages.

    Removes HTML/script tags to prevent XSS.
    """
    if not message:
        return ""

    # Strip all HTML tags
    cleaned = bleach.clean(message, tags=[], strip=True)

    # Limit message length (prevent abuse)
    max_length = 10000
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned.strip()
