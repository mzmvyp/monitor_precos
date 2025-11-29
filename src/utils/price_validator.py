"""Price validation utilities."""

import logging
from typing import Optional, Tuple, Dict, Any

LOGGER = logging.getLogger(__name__)


class PriceValidator:
    """Validates prices against configured limits and historical data."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize price validator with configuration.

        Args:
            config: Configuration dictionary with price_validation settings
        """
        self.config = config
        self.history_cache: Dict[str, float] = {}

    def validate(
        self,
        price: float,
        product_id: str,
        category: str,
        store: str,
        previous_price: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Validate price against limits and historical data.

        Args:
            price: Current price to validate
            product_id: Product identifier
            category: Product category (memory, motherboard, cpu, etc.)
            store: Store name
            previous_price: Previous price for comparison (optional)

        Returns:
            Tuple of (is_valid, reason)
            - is_valid: True if price is valid, False otherwise
            - reason: Explanation of validation result

        Examples:
            >>> validator = PriceValidator(config)
            >>> validator.validate(1000, "prod-1", "memory", "kabum")
            (True, "OK")
            >>> validator.validate(10, "prod-1", "memory", "kabum")
            (False, "Preço 10.00 abaixo do mínimo 150.0 para memory")
        """
        limits = self.config.get("price_validation", {})
        category_limits = limits.get("category_limits", {}).get(category, {})

        # 1. Check absolute limits
        min_price = category_limits.get("min", limits.get("min_price", 50))
        max_price = category_limits.get("max", limits.get("max_price", 50000))

        if price < min_price:
            return (
                False,
                f"Preço {price:.2f} abaixo do mínimo {min_price} para {category}",
            )

        if price > max_price:
            return (
                False,
                f"Preço {price:.2f} acima do máximo {max_price} para {category}",
            )

        # 2. Check variation against previous price
        if previous_price and previous_price > 0:
            change_percent = ((price - previous_price) / previous_price) * 100

            max_increase = limits.get("max_increase_percent", 150)
            max_decrease = limits.get("max_decrease_percent", 90)

            if change_percent > max_increase:
                return (
                    False,
                    f"Aumento de {change_percent:.1f}% suspeito (máx: {max_increase}%)",
                )

            if change_percent < -max_decrease:
                return (
                    False,
                    f"Queda de {abs(change_percent):.1f}% suspeita (máx: {max_decrease}%)",
                )

        return True, "OK"

    def update_history(self, product_id: str, price: float) -> None:
        """
        Update price history cache.

        Args:
            product_id: Product identifier
            price: Current price
        """
        self.history_cache[product_id] = price

    def get_previous_price(self, product_id: str) -> Optional[float]:
        """
        Get previous price from cache.

        Args:
            product_id: Product identifier

        Returns:
            Previous price or None if not cached
        """
        return self.history_cache.get(product_id)

    def clear_history(self) -> None:
        """Clear price history cache."""
        self.history_cache.clear()
        LOGGER.info("Price history cache cleared")
