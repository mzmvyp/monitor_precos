"""Tests for price validation utilities."""

import pytest
from src.utils.price_validator import PriceValidator


@pytest.fixture
def config():
    """Test configuration."""
    return {
        "price_validation": {
            "min_price": 50.0,
            "max_price": 50000.0,
            "max_increase_percent": 150,
            "max_decrease_percent": 90,
            "category_limits": {
                "memory": {
                    "min": 150,
                    "max": 5000,
                },
                "motherboard": {
                    "min": 400,
                    "max": 8000,
                },
                "cpu": {
                    "min": 300,
                    "max": 10000,
                },
            },
        }
    }


@pytest.fixture
def validator(config):
    """Create validator instance."""
    return PriceValidator(config)


class TestPriceValidatorBasicLimits:
    """Test basic price limit validation."""

    def test_price_within_limits(self, validator):
        """Test price within allowed limits"""
        is_valid, reason = validator.validate(1000, "prod-1", "memory", "kabum")
        assert is_valid
        assert reason == "OK"

    def test_price_below_minimum(self, validator):
        """Test price below minimum"""
        is_valid, reason = validator.validate(100, "prod-1", "memory", "kabum")
        assert not is_valid
        assert "abaixo do mínimo" in reason

    def test_price_above_maximum(self, validator):
        """Test price above maximum"""
        is_valid, reason = validator.validate(10000, "prod-1", "memory", "kabum")
        assert not is_valid
        assert "acima do máximo" in reason


class TestPriceValidatorCategoryLimits:
    """Test category-specific price limits."""

    def test_memory_category_limits(self, validator):
        """Test memory category limits (150-5000)"""
        assert validator.validate(200, "prod-1", "memory", "kabum")[0]
        assert validator.validate(4999, "prod-1", "memory", "kabum")[0]
        assert not validator.validate(100, "prod-1", "memory", "kabum")[0]
        assert not validator.validate(6000, "prod-1", "memory", "kabum")[0]

    def test_motherboard_category_limits(self, validator):
        """Test motherboard category limits (400-8000)"""
        assert validator.validate(500, "prod-1", "motherboard", "kabum")[0]
        assert validator.validate(7999, "prod-1", "motherboard", "kabum")[0]
        assert not validator.validate(300, "prod-1", "motherboard", "kabum")[0]
        assert not validator.validate(9000, "prod-1", "motherboard", "kabum")[0]

    def test_cpu_category_limits(self, validator):
        """Test CPU category limits (300-10000)"""
        assert validator.validate(500, "prod-1", "cpu", "kabum")[0]
        assert validator.validate(9999, "prod-1", "cpu", "kabum")[0]
        assert not validator.validate(200, "prod-1", "cpu", "kabum")[0]
        assert not validator.validate(11000, "prod-1", "cpu", "kabum")[0]

    def test_unknown_category_uses_defaults(self, validator):
        """Test unknown category uses default limits"""
        is_valid, reason = validator.validate(1000, "prod-1", "unknown", "kabum")
        assert is_valid  # Should use default limits (50-50000)


class TestPriceValidatorVariation:
    """Test price variation validation."""

    def test_reasonable_increase(self, validator):
        """Test reasonable price increase"""
        is_valid, reason = validator.validate(
            1200, "prod-1", "memory", "kabum", previous_price=1000
        )
        assert is_valid
        assert reason == "OK"

    def test_excessive_increase(self, validator):
        """Test excessive price increase (> 150%)"""
        is_valid, reason = validator.validate(
            3000, "prod-1", "memory", "kabum", previous_price=1000
        )
        assert not is_valid
        assert "Aumento" in reason
        assert "suspeito" in reason

    def test_reasonable_decrease(self, validator):
        """Test reasonable price decrease"""
        is_valid, reason = validator.validate(
            800, "prod-1", "memory", "kabum", previous_price=1000
        )
        assert is_valid
        assert reason == "OK"

    def test_excessive_decrease(self, validator):
        """Test excessive price decrease (> 90%)"""
        is_valid, reason = validator.validate(
            50, "prod-1", "memory", "kabum", previous_price=1000
        )
        assert not is_valid
        assert "Queda" in reason
        assert "suspeita" in reason

    def test_no_previous_price(self, validator):
        """Test validation without previous price"""
        is_valid, reason = validator.validate(1000, "prod-1", "memory", "kabum")
        assert is_valid
        assert reason == "OK"


class TestPriceValidatorHistory:
    """Test price history management."""

    def test_update_and_get_history(self, validator):
        """Test updating and retrieving price history"""
        validator.update_history("prod-1", 1000.0)
        assert validator.get_previous_price("prod-1") == 1000.0

    def test_get_nonexistent_history(self, validator):
        """Test getting price for non-existent product"""
        assert validator.get_previous_price("nonexistent") is None

    def test_clear_history(self, validator):
        """Test clearing price history"""
        validator.update_history("prod-1", 1000.0)
        validator.update_history("prod-2", 2000.0)
        validator.clear_history()
        assert validator.get_previous_price("prod-1") is None
        assert validator.get_previous_price("prod-2") is None
