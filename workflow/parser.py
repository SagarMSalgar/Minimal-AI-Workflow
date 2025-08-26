"""
Email Parser Component

Extracts structured data from inquiry emails including sender info, products,
quantities, urgency, and currency. Provides confidence scores and identifies gaps.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class EmailParser:
    """Parses inquiry emails and extracts structured data."""
    
    def __init__(self, price_list: Dict):
        self.price_list = price_list
        self.product_names = list(price_list.keys())
        
        # Compile regex patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.currency_pattern = re.compile(r'\b(USD|EUR|GBP|CAD|AUD|JPY)\b', re.IGNORECASE)
        self.urgency_pattern = re.compile(r'\b(asap|urgent|rush|immediate|quick|fast)\b', re.IGNORECASE)
        self.quantity_pattern = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:pcs?|pieces?|units?|kits?|packs?|boxes?|sets?)?\b', re.IGNORECASE)
        
    def parse_email(self, content: str, email_id: str) -> Dict:
        """Parse email content and extract structured data."""
        # Clean content
        clean_content = self._clean_content(content)
        
        # Extract components
        sender = self._extract_sender(clean_content)
        products = self._extract_products(clean_content)
        urgency = self._extract_urgency(clean_content)
        currency = self._extract_currency(clean_content)
        
        # Identify gaps
        gaps = self._identify_gaps(products, sender)
        
        return {
            "email_id": email_id,
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "products": products,
            "urgency": urgency,
            "currency": currency,
            "gaps": gaps,
            "raw_content": content
        }
    
    def _clean_content(self, content: str) -> str:
        """Clean email content for parsing."""
        # Remove quoted text (lines starting with >)
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            if not line.strip().startswith('>') and not line.strip().startswith('|'):
                clean_lines.append(line)
        
        # Remove signature blocks (common patterns)
        content = '\n'.join(clean_lines)
        
        # Remove common signature patterns
        signature_patterns = [
            r'--\s*\n.*',  # Lines after --
            r'Best regards,.*',
            r'Sincerely,.*',
            r'Thank you,.*',
            r'Regards,.*'
        ]
        
        for pattern in signature_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content.strip()
    
    def _extract_sender(self, content: str) -> Dict:
        """Extract sender information."""
        # Look for email addresses
        emails = self.email_pattern.findall(content)
        
        # Look for name patterns (common email formats)
        name_pattern = re.compile(r'From:\s*([^<]+?)\s*<[^>]+>', re.IGNORECASE)
        name_match = name_pattern.search(content)
        
        # Fallback for emails without angle brackets
        if not name_match:
            fallback_pattern = re.compile(r'From:\s*([^<\n]+)', re.IGNORECASE)
            name_match = fallback_pattern.search(content)
        
        sender_name = "Unknown"
        sender_email = emails[0] if emails else "unknown@example.com"
        confidence = 0.5
        
        if name_match:
            sender_name = name_match.group(1).strip()
            confidence = 0.8
        
        if emails:
            confidence = min(confidence + 0.2, 1.0)
        
        return {
            "name": sender_name,
            "email": sender_email,
            "confidence": confidence
        }
    
    def _extract_products(self, content: str) -> List[Dict]:
        """Extract product information from content."""
        products = []
        
        # Split content into lines for better product detection
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for product names in the line
            found_products = self._find_products_in_line(line)
            
            for product_name, quantity, unit in found_products:
                confidence = self._calculate_product_confidence(product_name, quantity, line)
                
                products.append({
                    "name": product_name,
                    "quantity": quantity,
                    "unit": unit,
                    "confidence": confidence,
                    "notes": self._generate_product_notes(product_name, quantity, unit)
                })
        
        # If no products found, try to extract from entire content
        if not products:
            found_products = self._find_products_in_line(content)
            for product_name, quantity, unit in found_products:
                confidence = self._calculate_product_confidence(product_name, quantity, content)
                
                products.append({
                    "name": product_name,
                    "quantity": quantity,
                    "unit": unit,
                    "confidence": confidence,
                    "notes": self._generate_product_notes(product_name, quantity, unit)
                })
        
        return products
    
    def _find_products_in_line(self, line: str) -> List[Tuple[str, Optional[float], Optional[str]]]:
        """Find products and their quantities in a line of text."""
        found_products = []
        
        # Look for each product name
        for product_name in self.product_names:
            # Case-insensitive search
            pattern = re.compile(re.escape(product_name), re.IGNORECASE)
            matches = pattern.finditer(line)
            
            for match in matches:
                # Look for quantity near the product name
                quantity, unit = self._extract_quantity_near_position(line, match.start())
                
                found_products.append((product_name, quantity, unit))
        
        return found_products
    
    def _extract_quantity_near_position(self, text: str, position: int) -> Tuple[Optional[float], Optional[str]]:
        """Extract quantity and unit near a specific position in text."""
        # Look for numbers before and after the position
        before_text = text[max(0, position-50):position]
        after_text = text[position:position+50]
        
        # Check for quantities before the product
        before_quantities = self.quantity_pattern.findall(before_text)
        if before_quantities:
            quantity = float(before_quantities[-1])  # Take the last one before the product
            unit = self._extract_unit(before_text, before_quantities[-1])
            return quantity, unit
        
        # Check for quantities after the product
        after_quantities = self.quantity_pattern.findall(after_text)
        if after_quantities:
            quantity = float(after_quantities[0])  # Take the first one after the product
            unit = self._extract_unit(after_text, after_quantities[0])
            return quantity, unit
        
        return None, None
    
    def _extract_unit(self, text: str, quantity: str) -> Optional[str]:
        """Extract unit of measurement from text near a quantity."""
        # Look for common units
        unit_patterns = [
            (r'pcs?|pieces?', 'piece'),
            (r'kits?', 'kit'),
            (r'packs?', 'pack'),
            (r'boxes?', 'box'),
            (r'sets?', 'set'),
            (r'units?', 'unit')
        ]
        
        for pattern, unit in unit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return unit
        
        return None
    
    def _calculate_product_confidence(self, product_name: str, quantity: Optional[float], context: str) -> float:
        """Calculate confidence score for a product extraction."""
        confidence = 0.5  # Base confidence
        
        # Product name exact match
        if product_name in self.product_names:
            confidence += 0.3
        
        # Quantity found
        if quantity is not None:
            confidence += 0.2
        
        # Context quality (length, clarity)
        if len(context.strip()) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_product_notes(self, product_name: str, quantity: Optional[float], unit: Optional[str]) -> str:
        """Generate notes about the product extraction."""
        notes = []
        
        if quantity is None:
            notes.append("Quantity not specified")
        
        if unit is None:
            notes.append("Unit not specified")
        
        if not notes:
            notes.append("Complete information extracted")
        
        return "; ".join(notes)
    
    def _extract_urgency(self, content: str) -> Optional[str]:
        """Extract urgency level from content."""
        urgency_matches = self.urgency_pattern.findall(content.lower())
        
        if not urgency_matches:
            return None
        
        # Determine urgency level based on keywords
        high_urgency = ['asap', 'urgent', 'rush', 'immediate']
        medium_urgency = ['quick', 'fast']
        
        for match in urgency_matches:
            if match in high_urgency:
                return 'high'
            elif match in medium_urgency:
                return 'medium'
        
        return 'low'
    
    def _extract_currency(self, content: str) -> Optional[str]:
        """Extract currency from content."""
        currency_matches = self.currency_pattern.findall(content)
        
        if currency_matches:
            return currency_matches[0].upper()
        
        return None
    
    def _identify_gaps(self, products: List[Dict], sender: Dict) -> List[str]:
        """Identify gaps in the extracted information."""
        gaps = []
        
        # Check sender information
        if sender['confidence'] < 0.7:
            gaps.append("Unclear sender information")
        
        # Check products
        if not products:
            gaps.append("No products identified")
        else:
            for product in products:
                if product['quantity'] is None:
                    gaps.append(f"Missing quantity for {product['name']}")
                
                if product['confidence'] < 0.6:
                    gaps.append(f"Low confidence in {product['name']} extraction")
        
        return gaps
