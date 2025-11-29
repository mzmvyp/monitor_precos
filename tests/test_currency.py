"""Tests for currency parsing utilities."""

import pytest
from src.utils.currency import parse_brazilian_currency, format_brazilian_currency


class TestParseBrazilianCurrency:
    """Test parse_brazilian_currency function."""

    def test_standard_format(self):
        """Test standard Brazilian format: R$ 1.234,56"""
        assert parse_brazilian_currency("R$ 1.234,56") == 1234.56

    def test_no_space_after_rs(self):
        """Test format without space: R$1234,56"""
        assert parse_brazilian_currency("R$1234,56") == 1234.56

    def test_integer_only(self):
        """Test integer values: R$ 1234"""
        assert parse_brazilian_currency("R$ 1234") == 1234.0

    def test_with_thousands_separator(self):
        """Test with thousands separator: R$ 12.345,67"""
        assert parse_brazilian_currency("R$ 12.345,67") == 12345.67

    def test_multiple_thousands_separators(self):
        """Test multiple thousands separators: R$ 1.234.567,89"""
        assert parse_brazilian_currency("R$ 1.234.567,89") == 1234567.89

    def test_no_cents(self):
        """Test format without cents: R$ 1.234"""
        assert parse_brazilian_currency("R$ 1.234") == 1234.0

    def test_extra_spaces(self):
        """Test with extra spaces: R$   1.234,56"""
        assert parse_brazilian_currency("R$   1.234,56") == 1234.56

    def test_missing_rs_prefix(self):
        """Test without R$ prefix (should fail)"""
        assert parse_brazilian_currency("1.234,56") is None

    def test_empty_string(self):
        """Test empty string"""
        assert parse_brazilian_currency("") is None

    def test_none_value(self):
        """Test None value"""
        assert parse_brazilian_currency(None) is None

    def test_invalid_format(self):
        """Test invalid format"""
        assert parse_brazilian_currency("ABC") is None
        assert parse_brazilian_currency("R$ ABC") is None


class TestFormatBrazilianCurrency:
    """Test format_brazilian_currency function."""

    def test_standard_formatting(self):
        """Test standard formatting"""
        assert format_brazilian_currency(1234.56) == "R$ 1.234,56"

    def test_integer_value(self):
        """Test integer value"""
        assert format_brazilian_currency(1234.0) == "R$ 1.234,00"

    def test_no_thousands_separator(self):
        """Test value without thousands"""
        assert format_brazilian_currency(999.90) == "R$ 999,90"

    def test_large_value(self):
        """Test large value"""
        assert format_brazilian_currency(1234567.89) == "R$ 1.234.567,89"

    def test_zero_value(self):
        """Test zero value"""
        assert format_brazilian_currency(0.0) == "R$ 0,00"

    def test_round_trip(self):
        """Test parsing and formatting round trip"""
        original = 1234.56
        formatted = format_brazilian_currency(original)
        parsed = parse_brazilian_currency(formatted)
        assert parsed == original
