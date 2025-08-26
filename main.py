#!/usr/bin/env python3
"""
Minimal AI Workflow: Email → Structured Data → Reply → Quote JSON

Main orchestrator for processing inquiry emails and generating structured outputs.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from workflow.parser import EmailParser
from workflow.acknowledgment import AcknowledgmentGenerator
from workflow.quote import QuoteGenerator
from workflow.logger import ActivityLogger


class WorkflowOrchestrator:
    """Main orchestrator for the AI workflow."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.logger = ActivityLogger()
        
        # Load configuration
        self.config = self._load_config()
        self.price_list = self._load_price_list()
        self.discount_rules = self._load_discount_rules()
        
        # Initialize components
        self.parser = EmailParser(self.price_list)
        self.ack_generator = AcknowledgmentGenerator(self.config)
        self.quote_generator = QuoteGenerator(
            self.price_list, 
            self.discount_rules, 
            self.config
        )
        
        # Create output directories
        self._ensure_directories()
    
    def _load_config(self) -> Dict:
        """Load system configuration."""
        config_file = self.config_dir / "defaults.json"
        if not config_file.exists():
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "tax_rate": 0.095,
            "default_currency": "USD",
            "quote_validity_days": 7,
            "sla_hours": 24,
            "company_name": "Acme Corp",
            "contact_email": "sales@acme.com"
        }
    
    def _load_price_list(self) -> Dict:
        """Load product price list."""
        price_file = self.config_dir / "price_list.json"
        if not price_file.exists():
            return self._get_default_price_list()
        
        with open(price_file, 'r') as f:
            return json.load(f)
    
    def _get_default_price_list(self) -> Dict:
        """Return default price list."""
        return {
            "Widget Pro": {"price": 25.00, "unit": "piece"},
            "Gadget Basic": {"price": 15.50, "unit": "piece"},
            "Tool Kit": {"price": 45.00, "unit": "kit"},
            "Premium Widget": {"price": 75.00, "unit": "piece"},
            "Bulk Pack": {"price": 200.00, "unit": "pack"}
        }
    
    def _load_discount_rules(self) -> Dict:
        """Load discount rules."""
        discount_file = self.config_dir / "discount_rules.json"
        if not discount_file.exists():
            return self._get_default_discount_rules()
        
        with open(discount_file, 'r') as f:
            return json.load(f)
    
    def _get_default_discount_rules(self) -> Dict:
        """Return default discount rules."""
        return {
            "tiers": [
                {"min_amount": 0, "max_amount": 100, "discount": 0.05},
                {"min_amount": 100, "max_amount": 500, "discount": 0.10},
                {"min_amount": 500, "max_amount": 1000, "discount": 0.15},
                {"min_amount": 1000, "max_amount": float('inf'), "discount": 0.20}
            ]
        }
    
    def _ensure_directories(self):
        """Create necessary output directories."""
        directories = [
            "data/events",
            "data/outbox", 
            "data/quotes",
            "data/timeline"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_email_id(self, content: str) -> str:
        """Generate a stable email ID from content."""
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _is_already_processed(self, email_id: str) -> bool:
        """Check if email has already been processed."""
        event_file = Path(f"data/events/{email_id}.json")
        return event_file.exists()
    
    def process_email(self, email_path: Path) -> bool:
        """Process a single email through the complete workflow."""
        try:
            # Read email content
            with open(email_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate stable ID
            email_id = self._generate_email_id(content)
            
            # Check if already processed
            if self._is_already_processed(email_id):
                self.logger.log("skip", email_id, f"Already processed: {email_path.name}")
                return True
            
            # Step 1: Parse email
            self.logger.log("start", email_id, f"Processing: {email_path.name}")
            parsed_event = self.parser.parse_email(content, email_id)
            
            # Save parsed event
            event_file = Path(f"data/events/{email_id}.json")
            with open(event_file, 'w') as f:
                json.dump(parsed_event, f, indent=2)
            
            self.logger.log("parse", email_id, f"Extracted {len(parsed_event['products'])} products")
            
            # Step 2: Generate acknowledgment
            acknowledgment = self.ack_generator.generate(parsed_event)
            
            # Save acknowledgment
            ack_file = Path(f"data/outbox/{email_id}_ack.json")
            with open(ack_file, 'w') as f:
                json.dump(acknowledgment, f, indent=2)
            
            self.logger.log("ack", email_id, f"Generated acknowledgment with {len(acknowledgment.get('questions', []))} questions")
            
            # Step 3: Generate quote
            quote = self.quote_generator.generate(parsed_event)
            
            # Save quote
            quote_file = Path(f"data/quotes/{email_id}.json")
            with open(quote_file, 'w') as f:
                json.dump(quote, f, indent=2)
            
            status = quote['status']
            self.logger.log("quote", email_id, f"Generated {status} quote: ${quote['total']:.2f}")
            
            return True
            
        except Exception as e:
            email_id = self._generate_email_id(content) if 'content' in locals() else "unknown"
            self.logger.log("error", email_id, f"Failed to process {email_path.name}: {str(e)}")
            return False
    
    def process_inbox(self, inbox_path: str) -> Dict:
        """Process all emails in the inbox directory."""
        inbox = Path(inbox_path)
        if not inbox.exists():
            raise ValueError(f"Inbox directory not found: {inbox_path}")
        
        # Find all .txt files
        email_files = list(inbox.glob("*.txt"))
        if not email_files:
            self.logger.log("info", "system", f"No .txt files found in {inbox_path}")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        self.logger.log("start", "system", f"Processing {len(email_files)} emails from {inbox_path}")
        
        processed = 0
        failed = 0
        skipped = 0
        
        for email_file in email_files:
            try:
                if self.process_email(email_file):
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.logger.log("error", "system", f"Unexpected error processing {email_file.name}: {str(e)}")
        
        self.logger.log("complete", "system", 
                       f"Workflow complete: {processed} processed, {failed} failed, {skipped} skipped")
        
        return {
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "total": len(email_files)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Minimal AI Workflow for Email Processing")
    parser.add_argument("command", choices=["process"], help="Command to execute")
    parser.add_argument("inbox_path", help="Path to inbox directory containing .txt emails")
    parser.add_argument("--config", default="config", help="Configuration directory")
    
    args = parser.parse_args()
    
    if args.command == "process":
        try:
            orchestrator = WorkflowOrchestrator(args.config)
            results = orchestrator.process_inbox(args.inbox_path)
            
            print(f"\nWorkflow Results:")
            print(f"  Processed: {results['processed']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Skipped: {results['skipped']}")
            print(f"  Total: {results['total']}")
            
            if results['failed'] > 0:
                sys.exit(1)
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
