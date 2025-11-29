"""Currency parsing and formatting utilities."""

import re
import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


def parse_brazilian_currency(value: str) -> Optional[float]:
    """
    Parse Brazilian currency string to float.

    Accepts formats:
    - R$ 1.234,56
    - R$1234,56
    - R$ 1234
    - R$ 1.234

    Args:
        value: Currency string to parse

    Returns:
        Float value or None if parsing fails

    Examples:
        >>> parse_brazilian_currency("R$ 1.234,56")
        1234.56
        >>> parse_brazilian_currency("R$1234,56")
        1234.56
        >>> parse_brazilian_currency("R$ 1234")
        1234.0
        >>> parse_brazilian_currency("1.234,56")  # Missing R$
        None
        >>> parse_brazilian_currency("")
        None
    """
    if not value:
        return None

    # Pattern: R$ 1.234,56 or R$1234,56 or R$ 1234 (with or without cents)
    match = re.search(r'R\$\s*([0-9\.\s]+(?:,[0-9]{1,2})?)', value)
    if not match:
        return None

    number = match.group(1)
    digits = number.replace(" ", "").replace(".", "")

    # If has comma, it's the decimal separator
    if "," in digits:
        digits = digits.replace(",", ".")
    # If no comma, it's already the integer value

    try:
        return float(digits)
    except ValueError:
        LOGGER.debug("Failed to convert price: %s", number)
        return None


def format_brazilian_currency(value: float) -> str:
    """
    Format float to Brazilian currency string.

    Args:
        value: Float value to format

    Returns:
        Formatted currency string

    Examples:
        >>> format_brazilian_currency(1234.56)
        'R$ 1.234,56'
        >>> format_brazilian_currency(1234.0)
        'R$ 1.234,00'
        >>> format_brazilian_currency(999.9)
        'R$ 999,90'
    """
    # Format with thousands separator and 2 decimal places
    formatted = f"{value:,.2f}"

    # Replace . with , for decimals and , with . for thousands
    # First replace , with a temporary placeholder
    formatted = formatted.replace(",", "TEMP")
    # Replace . with ,
    formatted = formatted.replace(".", ",")
    # Replace placeholder with .
    formatted = formatted.replace("TEMP", ".")

    return f"R$ {formatted}"
