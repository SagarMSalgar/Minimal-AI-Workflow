import pytest
from workflow.parser import EmailParser


class TestEmailParser:
    """Test cases for EmailParser."""
    
    @pytest.fixture
    def price_list(self):
        """Sample price list for testing."""
        return {
            "Widget Pro": {"price": 25.00, "unit": "piece"},
            "Gadget Basic": {"price": 15.50, "unit": "piece"},
            "Tool Kit": {"price": 45.00, "unit": "kit"}
        }
    
    @pytest.fixture
    def parser(self, price_list):
        """EmailParser instance for testing."""
        return EmailParser(price_list)
    
    def test_parse_complete_email(self, parser):
        """Test parsing an email with complete information."""
        content = """
        From: John Smith <john@example.com>
        
        Hi, I need 10 Widget Pro pieces for our project.
        Please quote in USD.
        """
        
        result = parser.parse_email(content, "test123")
        
        assert result["email_id"] == "test123"
        assert result["sender"]["name"] == "John Smith"
        assert result["sender"]["email"] == "john@example.com"
        assert len(result["products"]) == 1
        assert result["products"][0]["name"] == "Widget Pro"
        assert result["products"][0]["quantity"] == 10.0
        assert result["currency"] == "USD"
        assert len(result["gaps"]) == 0
    
    def test_parse_email_with_missing_quantity(self, parser):
        """Test parsing an email with missing quantity."""
        content = """
        From: Jane Doe <jane@example.com>
        
        I'm interested in Gadget Basic. Can you quote me?
        """
        
        result = parser.parse_email(content, "test456")
        
        assert result["products"][0]["name"] == "Gadget Basic"
        assert result["products"][0]["quantity"] is None
        assert "Missing quantity" in result["gaps"][0]
    
    def test_parse_email_with_multiple_products(self, parser):
        """Test parsing an email with multiple products."""
        content = """
        From: Bob Wilson <bob@example.com>
        
        Need 5 Widget Pro and 2 Tool Kit for our project.
        """
        
        result = parser.parse_email(content, "test789")
        
        assert len(result["products"]) == 2
        assert result["products"][0]["name"] == "Widget Pro"
        assert result["products"][0]["quantity"] == 5.0
        assert result["products"][1]["name"] == "Tool Kit"
        assert result["products"][1]["quantity"] == 2.0
    
    def test_parse_email_with_urgency(self, parser):
        """Test parsing an email with urgency indicators."""
        content = """
        From: Alice Brown <alice@example.com>
        
        Need 3 Gadget Basic asap! This is urgent.
        """
        
        result = parser.parse_email(content, "test101")
        
        assert result["urgency"] == "high"
        assert result["products"][0]["name"] == "Gadget Basic"
        assert result["products"][0]["quantity"] == 3.0
    
    def test_parse_email_with_unrecognized_product(self, parser):
        """Test parsing an email with unrecognized product."""
        content = """
        From: Charlie Davis <charlie@example.com>
        
        I need 5 Custom Product units.
        """
        
        result = parser.parse_email(content, "test202")
        
        assert len(result["products"]) == 0
        assert "No products identified" in result["gaps"]
    
    def test_parse_email_with_quoted_content(self, parser):
        """Test parsing an email with quoted content."""
        content = """
        From: Diana Evans <diana@example.com>
        
        > On Mon, Jan 15, 2024 at 10:00 AM, Sales wrote:
        > > Thank you for your inquiry
        
        Hi, I need 2 Tool Kit for our workshop.
        """
        
        result = parser.parse_email(content, "test303")
        
        assert result["products"][0]["name"] == "Tool Kit"
        assert result["products"][0]["quantity"] == 2.0
    
    def test_parse_email_with_signature(self, parser):
        """Test parsing an email with signature block."""
        content = """
        From: Frank Miller <frank@example.com>
        
        Please quote 10 Widget Pro.
        
        --
        Frank Miller
        CEO, Miller Corp
        Phone: (555) 123-4567
        """
        
        result = parser.parse_email(content, "test404")
        
        assert result["products"][0]["name"] == "Widget Pro"
        assert result["products"][0]["quantity"] == 10.0
    
    def test_parse_email_with_different_currency(self, parser):
        """Test parsing an email with different currency."""
        content = """
        From: Grace Lee <grace@example.com>
        
        Need 5 Gadget Basic. Please quote in EUR.
        """
        
        result = parser.parse_email(content, "test505")
        
        assert result["currency"] == "EUR"
        assert result["products"][0]["name"] == "Gadget Basic"
        assert result["products"][0]["quantity"] == 5.0
    
    def test_parse_email_with_informal_language(self, parser):
        """Test parsing an email with informal language."""
        content = """
        From: Henry Adams <henry@example.com>
        
        Hey there! Need 3 Widget Pro pieces asap. Thanks!
        """
        
        result = parser.parse_email(content, "test606")
        
        assert result["urgency"] == "high"
        assert result["products"][0]["name"] == "Widget Pro"
        assert result["products"][0]["quantity"] == 3.0
    
    def test_parse_email_with_no_sender_info(self, parser):
        """Test parsing an email with minimal sender information."""
        content = """
        Need 2 Tool Kit for our project.
        """
        
        result = parser.parse_email(content, "test707")
        
        assert result["sender"]["name"] == "Unknown"
        assert result["sender"]["confidence"] < 0.7
        assert "Unclear sender information" in result["gaps"]
    
    def test_parse_email_with_units(self, parser):
        """Test parsing an email with explicit units."""
        content = """
        From: Irene Clark <irene@example.com>
        
        I need 5 pieces of Widget Pro and 2 kits of Tool Kit.
        """
        
        result = parser.parse_email(content, "test808")
        
        assert result["products"][0]["name"] == "Widget Pro"
        assert result["products"][0]["quantity"] == 5.0
        assert result["products"][0]["unit"] == "piece"
        assert result["products"][1]["name"] == "Tool Kit"
        assert result["products"][1]["quantity"] == 2.0
        assert result["products"][1]["unit"] == "kit"
