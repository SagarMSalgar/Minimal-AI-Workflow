"""
Minimal AI Workflow Package

Contains components for email parsing, acknowledgment generation, quote computation,
and activity logging.
"""

from .parser import EmailParser
from .acknowledgment import AcknowledgmentGenerator
from .quote import QuoteGenerator
from .logger import ActivityLogger

__all__ = [
    'EmailParser',
    'AcknowledgmentGenerator', 
    'QuoteGenerator',
    'ActivityLogger'
]
