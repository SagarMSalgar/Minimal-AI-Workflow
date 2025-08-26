# AI Workflow — Email → Structured Data → Reply → Quote JSON

A minimal AI workflow system that processes email inquiries, extracts structured data, generates professional acknowledgments, and creates detailed quotes with pricing calculations.

## Overview

This application implements a complete email processing pipeline:

1. **Email Input** 📧 - Processes `.txt` email files from an inbox directory
2. **Structured Data Extraction** 🔍 - Parses emails to extract sender info, products, quantities, and requirements
3. **Reply Generation** ✉️ - Creates professional acknowledgment emails with follow-up questions
4. **Quote JSON Generation** 💰 - Generates detailed quotes with pricing, discounts, and taxes

## Quick Start

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Minimal-AI-Workflow
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Workflow

Process all emails in the sample inbox:
```bash
python main.py process samples/inbox
```

Process emails from a custom inbox directory:
```bash
python main.py process /path/to/your/inbox
```

### Output Structure

After running the workflow, the following directories will be populated:

```
data/
├── events/          # Parsed email data (JSON)
├── outbox/          # Generated acknowledgment emails (JSON)
├── quotes/          # Generated quotes (JSON)
└── timeline/        # Activity logs (JSONL)
```

## Configuration

The application uses three configuration files in the `config/` directory:

### `config/defaults.json`
```json
{
  "tax_rate": 0.095,
  "default_currency": "USD",
  "quote_validity_days": 7,
  "sla_hours": 24,
  "company_name": "Acme Corp",
  "contact_email": "sales@acme.com"
}
```

### `config/price_list.json`
```json
{
  "Widget Pro": {
    "price": 25.00,
    "unit": "piece",
    "description": "Professional grade widget with advanced features"
  },
  "Gadget Basic": {
    "price": 15.50,
    "unit": "piece",
    "description": "Basic gadget for everyday use"
  }
}
```

### `config/discount_rules.json`
```json
{
  "tiers": [
    {
      "min_amount": 0,
      "max_amount": 100,
      "discount": 0.05
    },
    {
      "min_amount": 100,
      "max_amount": 500,
      "discount": 0.10
    }
  ]
}
```

## Data Schemas

### Parsed Event Schema (`data/events/{email_id}.json`)

```json
{
  "email_id": "string",
  "timestamp": "ISO8601",
  "sender": {
    "name": "string",
    "email": "string",
    "confidence": "float (0.0-1.0)"
  },
  "products": [
    {
      "name": "string",
      "quantity": "float|null",
      "unit": "string|null",
      "confidence": "float (0.0-1.0)",
      "notes": "string"
    }
  ],
  "urgency": "string|null (high|medium|low)",
  "currency": "string|null",
  "gaps": ["string"],
  "raw_content": "string"
}
```

### Acknowledgment Schema (`data/outbox/{email_id}_ack.json`)

```json
{
  "email_id": "string",
  "timestamp": "ISO8601",
  "to": "string",
  "subject": "string",
  "greeting": "string",
  "body": "string",
  "questions": ["string"],
  "closing": "string",
  "sla_hours": "integer",
  "urgency_level": "string|null"
}
```

### Quote Schema (`data/quotes/{email_id}.json`)

#### Complete Quote
```json
{
  "email_id": "string",
  "timestamp": "ISO8601",
  "status": "complete",
  "line_items": [
    {
      "product": "string",
      "quantity": "float",
      "unit_price": "float",
      "total": "float",
      "unit": "string"
    }
  ],
  "subtotal": "float",
  "discount": "float",
  "tax": "float",
  "total": "float",
  "currency": "string",
  "pending_reasons": [],
  "valid_until": "ISO8601",
  "discount_rate": "float"
}
```

#### Pending Quote
```json
{
  "email_id": "string",
  "timestamp": "ISO8601",
  "status": "pending",
  "line_items": [],
  "subtotal": 0.0,
  "discount": 0.0,
  "tax": 0.0,
  "total": 0.0,
  "currency": "string|null",
  "pending_reasons": ["string"],
  "valid_until": "ISO8601",
  "discount_rate": 0.0
}
```

## Example Outputs


**Input Email** (`samples/inbox/email_001.txt`):
```
From: John Smith <john.smith@example.com>
Subject: Quote Request - Widget Pro

Hi there,

I need a quote for 10 Widget Pro units. This is for our upcoming project and we need them delivered within the next two weeks.

Please let me know the total cost including shipping to our address in New York.

Thanks,
John Smith
ABC Company
```

**Parsed Event** (`data/events/351e9b26.json`):
```json
{
  "email_id": "351e9b26",
  "timestamp": "2025-08-25T18:25:41.258603",
  "sender": {
    "name": "Maria Garcia",
    "email": "maria.garcia@global.com",
    "confidence": 1.0
  },
  "products": [
    {
      "name": "Gadget Basic",
      "quantity": 15.0,
      "unit": null,
      "confidence": 1.0,
      "notes": "Unit not specified"
    },
    {
      "name": "Special Item",
      "quantity": 2.0,
      "unit": null,
      "confidence": 1.0,
      "notes": "Unit not specified"
    }
  ],
  "urgency": null,
  "currency": "EUR",
  "gaps": [],
  "raw_content": "..."
}
```

**Acknowledgment** (`data/outbox/351e9b26_ack.json`):
```json
{
  "email_id": "351e9b26",
  "timestamp": "2025-08-25T18:25:41.259907",
  "to": "maria.garcia@global.com",
  "subject": "Re: Gadget Basic and Special Item Quote Request",
  "greeting": "Dear Maria Garcia,",
  "body": "Thank you for your inquiry. We appreciate your interest in Acme Corp products.\n\nWe have received your inquiry about the following products: Gadget Basic, Special Item.\n\nWe have all the necessary information to prepare your quote.\n\nWe will provide your quote within 24 hours. If you have any questions, please don't hesitate to contact us at sales@acme.com.",
  "questions": [
    "Do you have any specific delivery requirements or timeline preferences?"
  ],
  "closing": "Best regards,\n\nAcme Corp Sales Team\nsales@acme.com",
  "sla_hours": 24,
  "urgency_level": null
}
```

**Complete Quote** (`data/quotes/351e9b26.json`):
```json
{
  "email_id": "351e9b26",
  "timestamp": "2025-08-25T18:25:41.260869",
  "status": "complete",
  "line_items": [
    {
      "product": "Gadget Basic",
      "quantity": 15.0,
      "unit_price": 15.5,
      "total": 232.5,
      "unit": "piece"
    },
    {
      "product": "Special Item",
      "quantity": 2.0,
      "unit_price": 35.0,
      "total": 70.0,
      "unit": "piece"
    }
  ],
  "subtotal": 302.5,
  "discount": 30.25,
  "tax": 25.86,
  "total": 298.11,
  "currency": "EUR",
  "pending_reasons": [],
  "valid_until": "2025-09-01T18:25:41.260856",
  "discount_rate": 10.0
}
```


**Input Email** :
```
From: Alex Thompson <alex@smallbiz.com>
Subject: Re: Re: Re: Product Inquiry

Hi again,

I'm still interested in the Tool Kit. Can you send me a quote for 2 kits?

Also, what's the difference between Widget Pro and Gadget Basic?

Thanks,
Alex
```

**Parsed Event** (`data/events/9461b2dd.json`):
```json
{
  "email_id": "9461b2dd",
  "timestamp": "2025-08-25T18:25:41.238910",
  "sender": {
    "name": "Alex Thompson",
    "email": "alex@smallbiz.com",
    "confidence": 1.0
  },
  "products": [
    {
      "name": "Tool Kit",
      "quantity": 2.0,
      "unit": "kit",
      "confidence": 1.0,
      "notes": "Complete information extracted"
    },
    {
      "name": "Widget Pro",
      "quantity": null,
      "unit": null,
      "confidence": 0.9,
      "notes": "Quantity not specified; Unit not specified"
    },
    {
      "name": "Gadget Basic",
      "quantity": null,
      "unit": null,
      "confidence": 0.9,
      "notes": "Quantity not specified; Unit not specified"
    }
  ],
  "urgency": null,
  "currency": null,
  "gaps": [
    "Missing quantity for Widget Pro",
    "Missing quantity for Gadget Basic"
  ],
  "raw_content": "..."
}
```

**Acknowledgment** (`data/outbox/9461b2dd_ack.json`):
```json
{
  "email_id": "9461b2dd",
  "timestamp": "2025-08-25T18:25:41.239988",
  "to": "alex@smallbiz.com",
  "subject": "Re: Quote Request for 3 Items",
  "greeting": "Dear Alex Thompson,",
  "body": "Thank you for your inquiry. We appreciate your interest in Acme Corp products.\n\nWe have received your inquiry about the following products: Tool Kit, Widget Pro, Gadget Basic.\n\nTo provide you with an accurate quote, we need some additional information about your requirements.\n\nWe will provide your quote within 24 hours. If you have any questions, please don't hesitate to contact us at sales@acme.com.",
  "questions": [
    "What quantity of Widget Pro do you need?",
    "What quantity of Gadget Basic do you need?"
  ],
  "closing": "Best regards,\n\nAcme Corp Sales Team\nsales@acme.com",
  "sla_hours": 24,
  "urgency_level": null
}
```

**Pending Quote** (`data/quotes/9461b2dd.json`):
```json
{
  "email_id": "9461b2dd",
  "timestamp": "2025-08-25T18:25:41.242046",
  "status": "pending",
  "line_items": [],
  "subtotal": 0.0,
  "discount": 0.0,
  "tax": 0.0,
  "total": 0.0,
  "currency": null,
  "pending_reasons": [
    "Missing quantity for Widget Pro",
    "Missing quantity for Gadget Basic"
  ],
  "valid_until": "2025-09-01T18:25:41.242030",
  "discount_rate": 0.0
}
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

