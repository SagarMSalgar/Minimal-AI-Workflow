"""
Tests for the Quote Generator component.
"""

import pytest
from workflow.quote import QuoteGenerator


class TestQuoteGenerator:
    """Test cases for QuoteGenerator."""
    
    @pytest.fixture
    def price_list(self):
        """Sample price list for testing."""
        return {
            "Widget Pro": {"price": 25.00, "unit": "piece"},
            "Gadget Basic": {"price": 15.50, "unit": "piece"},
            "Tool Kit": {"price": 45.00, "unit": "kit"}
        }
    
    @pytest.fixture
    def discount_rules(self):
        """Sample discount rules for testing."""
        return {
            "tiers": [
                {"min_amount": 0, "max_amount": 100, "discount": 0.05},
                {"min_amount": 100, "max_amount": 500, "discount": 0.10},
                {"min_amount": 500, "max_amount": 1000, "discount": 0.15},
                {"min_amount": 1000, "max_amount": float('inf'), "discount": 0.20}
            ]
        }
    
    @pytest.fixture
    def config(self):
        """Sample configuration for testing."""
        return {
            "tax_rate": 0.095,
            "default_currency": "USD",
            "quote_validity_days": 7
        }
    
    @pytest.fixture
    def generator(self, price_list, discount_rules, config):
        """QuoteGenerator instance for testing."""
        return QuoteGenerator(price_list, discount_rules, config)
    
    def test_generate_complete_quote(self, generator):
        """Test generating a complete quote with all information."""
        parsed_event = {
            "email_id": "test123",
            "products": [
                {"name": "Widget Pro", "quantity": 10, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        assert quote["status"] == "complete"
        assert quote["email_id"] == "test123"
        assert len(quote["line_items"]) == 1
        assert quote["line_items"][0]["product"] == "Widget Pro"
        assert quote["line_items"][0]["quantity"] == 10
        assert quote["line_items"][0]["unit_price"] == 25.00
        assert quote["line_items"][0]["total"] == 250.00
        assert quote["subtotal"] == 250.00
        assert quote["currency"] == "USD"
        assert len(quote["pending_reasons"]) == 0
    
    def test_generate_pending_quote_missing_quantity(self, generator):
        """Test generating a pending quote when quantity is missing."""
        parsed_event = {
            "email_id": "test456",
            "products": [
                {"name": "Widget Pro", "quantity": None, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        assert quote["status"] == "pending"
        assert quote["total"] == 0.00
        assert "Missing quantity for Widget Pro" in quote["pending_reasons"]
    
    def test_generate_pending_quote_unrecognized_product(self, generator):
        """Test generating a pending quote for unrecognized product."""
        parsed_event = {
            "email_id": "test789",
            "products": [
                {"name": "Custom Product", "quantity": 5, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        assert quote["status"] == "pending"
        assert quote["total"] == 0.00
        assert "Unrecognized product: 'Custom Product'" in quote["pending_reasons"]
    
    def test_generate_pending_quote_no_products(self, generator):
        """Test generating a pending quote when no products are identified."""
        parsed_event = {
            "email_id": "test101",
            "products": [],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        assert quote["status"] == "pending"
        assert quote["total"] == 0.00
        assert "No products identified" in quote["pending_reasons"]
    
    def test_calculate_discount_tier_1(self, generator):
        """Test discount calculation for tier 1 (0-100)."""
        parsed_event = {
            "email_id": "test202",
            "products": [
                {"name": "Gadget Basic", "quantity": 5, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        # 5 * 15.50 = 77.50 (tier 1: 5% discount)
        expected_subtotal = 77.50
        expected_discount = 77.50 * 0.05
        expected_tax = (77.50 - expected_discount) * 0.095
        
        assert quote["subtotal"] == expected_subtotal
        assert quote["discount"] == round(expected_discount, 2)
        assert quote["tax"] == round(expected_tax, 2)
    
    def test_calculate_discount_tier_2(self, generator):
        """Test discount calculation for tier 2 (100-500)."""
        parsed_event = {
            "email_id": "test303",
            "products": [
                {"name": "Widget Pro", "quantity": 8, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        # 8 * 25.00 = 200.00 (tier 2: 10% discount)
        expected_subtotal = 200.00
        expected_discount = 200.00 * 0.10
        expected_tax = (200.00 - expected_discount) * 0.095
        
        assert quote["subtotal"] == expected_subtotal
        assert quote["discount"] == round(expected_discount, 2)
        assert quote["tax"] == round(expected_tax, 2)
    
    def test_calculate_discount_tier_3(self, generator):
        """Test discount calculation for tier 3 (500-1000)."""
        parsed_event = {
            "email_id": "test404",
            "products": [
                {"name": "Widget Pro", "quantity": 25, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        # 25 * 25.00 = 625.00 (tier 3: 15% discount)
        expected_subtotal = 625.00
        expected_discount = 625.00 * 0.15
        expected_tax = (625.00 - expected_discount) * 0.095
        
        assert quote["subtotal"] == expected_subtotal
        assert quote["discount"] == round(expected_discount, 2)
        assert quote["tax"] == round(expected_tax, 2)
    
    def test_calculate_discount_tier_4(self, generator):
        """Test discount calculation for tier 4 (1000+)."""
        parsed_event = {
            "email_id": "test505",
            "products": [
                {"name": "Widget Pro", "quantity": 50, "unit": "piece"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        # 50 * 25.00 = 1250.00 (tier 4: 20% discount)
        expected_subtotal = 1250.00
        expected_discount = 1250.00 * 0.20
        expected_tax = (1250.00 - expected_discount) * 0.095
        
        assert quote["subtotal"] == expected_subtotal
        assert quote["discount"] == round(expected_discount, 2)
        assert quote["tax"] == round(expected_tax, 2)
    
    def test_multiple_line_items(self, generator):
        """Test quote generation with multiple line items."""
        parsed_event = {
            "email_id": "test606",
            "products": [
                {"name": "Widget Pro", "quantity": 5, "unit": "piece"},
                {"name": "Tool Kit", "quantity": 2, "unit": "kit"}
            ],
            "currency": "USD"
        }
        
        quote = generator.generate(parsed_event)
        
        assert len(quote["line_items"]) == 2
        assert quote["line_items"][0]["product"] == "Widget Pro"
        assert quote["line_items"][0]["total"] == 125.00  # 5 * 25.00
        assert quote["line_items"][1]["product"] == "Tool Kit"
        assert quote["line_items"][1]["total"] == 90.00   # 2 * 45.00
        assert quote["subtotal"] == 215.00  # 125 + 90
    
    def test_different_currency(self, generator):
        """Test quote generation with different currency."""
        parsed_event = {
            "email_id": "test707",
            "products": [
                {"name": "Widget Pro", "quantity": 10, "unit": "piece"}
            ],
            "currency": "EUR"
        }
        
        quote = generator.generate(parsed_event)
        
        assert quote["currency"] == "EUR"
        assert quote["status"] == "complete"
    
    def test_quote_summary_complete(self, generator):
        """Test quote summary generation for complete quote."""
        quote = {
            "status": "complete",
            "line_items": [
                {"quantity": 10, "product": "Widget Pro"}
            ],
            "total": 261.25,
            "currency": "USD"
        }
        
        summary = generator.get_quote_summary(quote)
        assert "10 Widget Pro" in summary
        assert "USD 261.25" in summary
    
    def test_quote_summary_pending(self, generator):
        """Test quote summary generation for pending quote."""
        quote = {
            "status": "pending",
            "pending_reasons": ["Missing quantity for Widget Pro"]
        }
        
        summary = generator.get_quote_summary(quote)
        assert "Quote pending" in summary
        assert "Missing quantity" in summary
    
    def test_validate_quote_complete(self, generator):
        """Test quote validation for complete quote."""
        quote = {
            "email_id": "test808",
            "timestamp": "2024-01-15T10:30:00Z",
            "status": "complete",
            "line_items": [
                {"product": "Widget Pro", "quantity": 10, "unit_price": 25.00, "total": 250.00}
            ],
            "subtotal": 250.00,
            "discount": 12.50,
            "tax": 22.56,
            "total": 260.06,
            "currency": "USD",
            "pending_reasons": [],
            "valid_until": "2024-01-22T10:30:00Z"
        }
        
        errors = generator.validate_quote(quote)
        assert len(errors) == 0
    
    def test_validate_quote_pending(self, generator):
        """Test quote validation for pending quote."""
        quote = {
            "email_id": "test909",
            "timestamp": "2024-01-15T10:30:00Z",
            "status": "pending",
            "line_items": [],
            "subtotal": 0.00,
            "discount": 0.00,
            "tax": 0.00,
            "total": 0.00,
            "currency": "USD",
            "pending_reasons": ["Missing quantity for Widget Pro"],
            "valid_until": "2024-01-22T10:30:00Z"
        }
        
        errors = generator.validate_quote(quote)
        assert len(errors) == 0
    
    def test_validate_quote_invalid(self, generator):
        """Test quote validation for invalid quote."""
        quote = {
            "email_id": "test1010",
            "status": "complete",
            "total": 0.00  # Missing required fields
        }
        
        errors = generator.validate_quote(quote)
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)
