from datetime import datetime
from typing import Dict, List, Optional


class AcknowledgmentGenerator:
    """Generates professional acknowledgment emails."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.company_name = config.get("company_name", "Acme Corp")
        self.contact_email = config.get("contact_email", "sales@acme.com")
        self.sla_hours = config.get("sla_hours", 24)
    
    def generate(self, parsed_event: Dict) -> Dict:
        """Generate acknowledgment for a parsed email event."""
        email_id = parsed_event["email_id"]
        sender = parsed_event["sender"]
        products = parsed_event["products"]
        urgency = parsed_event["urgency"]
        gaps = parsed_event["gaps"]
        
        # Generate acknowledgment content
        subject = self._generate_subject(products, urgency)
        greeting = self._generate_greeting(sender)
        body = self._generate_body(parsed_event)
        closing = self._generate_closing()
        
        # Generate questions based on gaps
        questions = self._generate_questions(gaps, products)
        
        return {
            "email_id": email_id,
            "timestamp": datetime.now().isoformat(),
            "to": sender["email"],
            "subject": subject,
            "greeting": greeting,
            "body": body,
            "questions": questions,
            "closing": closing,
            "sla_hours": self.sla_hours,
            "urgency_level": urgency
        }
    
    def _generate_subject(self, products: List[Dict], urgency: Optional[str]) -> str:
        """Generate email subject line."""
        if not products:
            return "Re: Your Inquiry - Additional Information Needed"
        
        product_names = [p["name"] for p in products]
        
        if len(product_names) == 1:
            subject = f"Re: {product_names[0]} Quote Request"
        elif len(product_names) == 2:
            subject = f"Re: {product_names[0]} and {product_names[1]} Quote Request"
        else:
            subject = f"Re: Quote Request for {len(product_names)} Items"
        
        if urgency == "high":
            subject += " - URGENT"
        elif urgency == "medium":
            subject += " - Priority"
        
        return subject
    
    def _generate_greeting(self, sender: Dict) -> str:
        """Generate personalized greeting."""
        name = sender["name"]
        
        if name and name != "Unknown":
            return f"Dear {name},"
        else:
            return "Dear Valued Customer,"
    
    def _generate_body(self, parsed_event: Dict) -> str:
        """Generate the main body of the acknowledgment."""
        products = parsed_event["products"]
        gaps = parsed_event["gaps"]
        urgency = parsed_event["urgency"]
        
        body_parts = []
        
        # Thank you and acknowledgment
        body_parts.append(self._generate_thanks(urgency))
        
        # Reference extracted information
        if products:
            body_parts.append(self._reference_products(products))
        
        # Address gaps or confirm completeness
        if gaps:
            body_parts.append(self._address_gaps(gaps))
        else:
            body_parts.append(self._confirm_completeness())
        
        # Next steps
        body_parts.append(self._next_steps(urgency))
        
        return "\n\n".join(body_parts)
    
    def _generate_thanks(self, urgency: Optional[str]) -> str:
        """Generate thank you message with urgency consideration."""
        if urgency == "high":
            return f"Thank you for your urgent inquiry. We understand the time-sensitive nature of your request and will prioritize your quote accordingly."
        elif urgency == "medium":
            return f"Thank you for your inquiry. We appreciate your interest in our products and will process your request promptly."
        else:
            return f"Thank you for your inquiry. We appreciate your interest in {self.company_name} products."
    
    def _reference_products(self, products: List[Dict]) -> str:
        """Reference the products mentioned in the inquiry."""
        if len(products) == 1:
            product = products[0]
            if product["quantity"]:
                return f"We have received your request for {product['quantity']} {product['name']}."
            else:
                return f"We have received your inquiry about {product['name']}."
        else:
            product_names = [p["name"] for p in products]
            return f"We have received your inquiry about the following products: {', '.join(product_names)}."
    
    def _address_gaps(self, gaps: List[str]) -> str:
        """Address identified gaps in the inquiry."""
        if len(gaps) == 1:
            return f"To provide you with an accurate quote, we need some additional information: {gaps[0].lower()}"
        else:
            return f"To provide you with an accurate quote, we need some additional information about your requirements."
    
    def _confirm_completeness(self) -> str:
        """Confirm that all necessary information has been received."""
        return "We have all the necessary information to prepare your quote."
    
    def _next_steps(self, urgency: Optional[str]) -> str:
        """Describe next steps based on urgency."""
        if urgency == "high":
            return f"We will provide your quote within {self.sla_hours//2} hours. If you have any questions, please don't hesitate to contact us at {self.contact_email}."
        else:
            return f"We will provide your quote within {self.sla_hours} hours. If you have any questions, please don't hesitate to contact us at {self.contact_email}."
    
    def _generate_questions(self, gaps: List[str], products: List[Dict]) -> List[str]:
        """Generate specific questions based on identified gaps."""
        questions = []
        
        # Limit to 2 questions as specified
        max_questions = 2
        question_count = 0
        
        for gap in gaps:
            if question_count >= max_questions:
                break
                
            if "quantity" in gap.lower():
                for product in products:
                    if product["quantity"] is None:
                        questions.append(f"What quantity of {product['name']} do you need?")
                        question_count += 1
                        break
            
            elif "product" in gap.lower() and "unrecognized" in gap.lower():
                questions.append("Could you please provide more details about the specific products you're interested in?")
                question_count += 1
            
            elif "sender" in gap.lower():
                questions.append("Could you please confirm your contact information for our records?")
                question_count += 1
        
        # If no specific gaps, ask general questions
        if not questions and question_count < max_questions:
            if not products:
                questions.append("What products are you interested in purchasing?")
                question_count += 1
            
            if question_count < max_questions:
                questions.append("Do you have any specific delivery requirements or timeline preferences?")
        
        return questions[:max_questions]
    
    def _generate_closing(self) -> str:
        """Generate professional closing."""
        return f"Best regards,\n\n{self.company_name} Sales Team\n{self.contact_email}"
