"""Cloudflare challenge detection utilities."""

import time
import asyncio
import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)

# Cloudflare challenge signatures (English and Portuguese)
CLOUDFLARE_SIGNATURES = [
    # English
    "Just a moment",
    "Checking your browser",
    "Please enable cookies",
    "Please wait while we verify",
    "Attention Required",
    "One more step",
    "Verifying you are human",
    "This process is automatic",

    # Portuguese
    "Verificando seu navegador",
    "Um momento",
    "aguarde",
    "Ative os cookies",
    "Atenção necessária",
    "Mais um passo",
    "Verificando se você é humano",
    "Este processo é automático",

    # Technical identifiers
    "cf-browser-verification",
    "cf_chl_opt",
    "__cf_bm",
    "challenge-platform",
    "ray ID",
    "cloudflare-static",
    "cf-challenge",
]


def is_cloudflare_challenge(html: str) -> bool:
    """
    Check if HTML content contains Cloudflare challenge.

    Args:
        html: HTML content to check

    Returns:
        True if Cloudflare challenge detected, False otherwise

    Examples:
        >>> is_cloudflare_challenge("<html>Just a moment...</html>")
        True
        >>> is_cloudflare_challenge("<html>Normal content</html>")
        False
    """
    if not html:
        return False

    html_lower = html.lower()
    detected = any(sig.lower() in html_lower for sig in CLOUDFLARE_SIGNATURES)

    if detected:
        LOGGER.warning("Cloudflare challenge detected in HTML")

    return detected


async def wait_for_cloudflare(driver, max_wait: int = 60) -> bool:
    """
    Wait for Cloudflare challenge to resolve.

    Args:
        driver: Selenium WebDriver instance
        max_wait: Maximum time to wait in seconds (default: 60)

    Returns:
        True if challenge passed, False if timeout

    Examples:
        >>> async with driver:
        ...     success = await wait_for_cloudflare(driver, max_wait=30)
        ...     if success:
        ...         print("Challenge passed!")
    """
    start = time.time()
    check_interval = 2  # Check every 2 seconds

    LOGGER.info(f"Waiting for Cloudflare challenge to resolve (max {max_wait}s)...")

    while time.time() - start < max_wait:
        try:
            html = driver.page_source
            if not is_cloudflare_challenge(html):
                elapsed = time.time() - start
                LOGGER.info(f"Cloudflare challenge passed after {elapsed:.1f}s")
                return True

            await asyncio.sleep(check_interval)
        except Exception as e:
            LOGGER.error(f"Error checking Cloudflare status: {e}")
            return False

    LOGGER.error(f"Cloudflare challenge timeout after {max_wait}s")
    return False


def wait_for_cloudflare_sync(driver, max_wait: int = 60) -> bool:
    """
    Synchronous version of wait_for_cloudflare.

    Args:
        driver: Selenium WebDriver instance
        max_wait: Maximum time to wait in seconds (default: 60)

    Returns:
        True if challenge passed, False if timeout
    """
    start = time.time()
    check_interval = 2  # Check every 2 seconds

    LOGGER.info(f"Waiting for Cloudflare challenge to resolve (max {max_wait}s)...")

    while time.time() - start < max_wait:
        try:
            html = driver.page_source
            if not is_cloudflare_challenge(html):
                elapsed = time.time() - start
                LOGGER.info(f"Cloudflare challenge passed after {elapsed:.1f}s")
                return True

            time.sleep(check_interval)
        except Exception as e:
            LOGGER.error(f"Error checking Cloudflare status: {e}")
            return False

    LOGGER.error(f"Cloudflare challenge timeout after {max_wait}s")
    return False
