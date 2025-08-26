"""
Quote Generator Component

Computes quotes using local pricing and discount rules. Handles pending cases
when required information is missing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class QuoteGenerator:
    """Generates quotes with pricing and discount calculations."""
    
    def __init__(self, price_list: Dict, discount_rules: Dict, config: Dict):
        self.price_list = price_list
        self.discount_rules = discount_rules
        self.config = config
        
        self.tax_rate = config.get("tax_rate", 0.095)
        self.default_currency = config.get("default_currency", "USD")
        self.validity_days = config.get("quote_validity_days", 7)
    
    def generate(self, parsed_event: Dict) -> Dict:
        """Generate quote for a parsed email event."""
        email_id = parsed_event["email_id"]
        products = parsed_event["products"]
        currency = parsed_event.get("currency", self.default_currency)
        
        # Check if we have enough information for a complete quote
        can_generate_complete = self._can_generate_complete_quote(products)
        
        if can_generate_complete:
            return self._generate_complete_quote(email_id, products, currency)
        else:
            return self._generate_pending_quote(email_id, products, currency)
    
    def _can_generate_complete_quote(self, products: List[Dict]) -> bool:
        """Check if we have enough information to generate a complete quote."""
        if not products:
            return False
        
        for product in products:
            # Check if product exists in price list
            if product["name"] not in self.price_list:
                return False
            
            # Check if quantity is specified
            if product["quantity"] is None:
                return False
        
        return True
    
    def _generate_complete_quote(self, email_id: str, products: List[Dict], currency: str) -> Dict:
        """Generate a complete quote with all calculations."""
        line_items = []
        subtotal = 0.0
        
        # Process each product
        for product in products:
            product_name = product["name"]
            quantity = product["quantity"]
            
            # Get pricing information
            price_info = self.price_list[product_name]
            unit_price = price_info["price"]
            unit = price_info.get("unit", "piece")
            
            # Calculate line item total
            line_total = unit_price * quantity
            
            line_items.append({
                "product": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": line_total,
                "unit": unit
            })
            
            subtotal += line_total
        
        # Apply discount
        discount_rate = self._calculate_discount_rate(subtotal)
        discount_amount = subtotal * discount_rate
        
        # Calculate tax
        taxable_amount = subtotal - discount_amount
        tax_amount = taxable_amount * self.tax_rate
        
        # Calculate total
        total = subtotal - discount_amount + tax_amount
        
        # Calculate validity date
        valid_until = datetime.now() + timedelta(days=self.validity_days)
        
        return {
            "email_id": email_id,
            "timestamp": datetime.now().isoformat(),
            "status": "complete",
            "line_items": line_items,
            "subtotal": round(subtotal, 2),
            "discount": round(discount_amount, 2),
            "tax": round(tax_amount, 2),
            "total": round(total, 2),
            "currency": currency,
            "pending_reasons": [],
            "valid_until": valid_until.isoformat(),
            "discount_rate": round(discount_rate * 100, 1)
        }
    
    def _generate_pending_quote(self, email_id: str, products: List[Dict], currency: str) -> Dict:
        """Generate a pending quote when information is missing."""
        pending_reasons = []
        
        if not products:
            pending_reasons.append("No products identified in the inquiry")
        else:
            for product in products:
                if product["name"] not in self.price_list:
                    pending_reasons.append(f"Unrecognized product: '{product['name']}'")
                
                if product["quantity"] is None:
                    pending_reasons.append(f"Missing quantity for {product['name']}")
        
        # Calculate validity date
        valid_until = datetime.now() + timedelta(days=self.validity_days)
        
        return {
            "email_id": email_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "line_items": [],
            "subtotal": 0.00,
            "discount": 0.00,
            "tax": 0.00,
            "total": 0.00,
            "currency": currency,
            "pending_reasons": pending_reasons,
            "valid_until": valid_until.isoformat(),
            "discount_rate": 0.0
        }
    
    def _calculate_discount_rate(self, subtotal: float) -> float:
        """Calculate discount rate based on subtotal and discount rules."""
        tiers = self.discount_rules.get("tiers", [])
        
        # Find applicable tier
        for tier in tiers:
            min_amount = tier.get("min_amount", 0)
            max_amount = tier.get("max_amount", float('inf'))
            discount = tier.get("discount", 0)
            
            if min_amount <= subtotal < max_amount:
                return discount
        
        return 0.0
    
    def get_quote_summary(self, quote: Dict) -> str:
        """Generate a human-readable summary of the quote."""
        if quote["status"] == "pending":
            reasons = ", ".join(quote["pending_reasons"])
            return f"Quote pending: {reasons}"
        
        line_items = quote["line_items"]
        if len(line_items) == 1:
            item = line_items[0]
            return f"{item['quantity']} {item['product']} - {quote['currency']} {quote['total']:.2f}"
        else:
            return f"{len(line_items)} items - {quote['currency']} {quote['total']:.2f}"
    
    def validate_quote(self, quote: Dict) -> List[str]:
        """Validate quote for consistency and completeness."""
        errors = []
        
        # Check required fields
        required_fields = ["email_id", "timestamp", "status", "line_items", "subtotal", 
                          "discount", "tax", "total", "currency", "pending_reasons", "valid_until"]
        
        for field in required_fields:
            if field not in quote:
                errors.append(f"Missing required field: {field}")
        
        # Validate status-specific requirements
        if quote.get("status") == "complete":
            if not quote.get("line_items"):
                errors.append("Complete quote must have line items")
            
            if quote.get("total", 0) <= 0:
                errors.append("Complete quote must have positive total")
        
        elif quote.get("status") == "pending":
            if quote.get("total", 0) != 0:
                errors.append("Pending quote must have zero total")
            
            if not quote.get("pending_reasons"):
                errors.append("Pending quote must have pending reasons")
        
        # Validate calculations for complete quotes
        if quote.get("status") == "complete" and quote.get("line_items"):
            calculated_subtotal = sum(item.get("total", 0) for item in quote["line_items"])
            if abs(calculated_subtotal - quote.get("subtotal", 0)) > 0.01:
                errors.append("Subtotal calculation mismatch")
        
        return errors
