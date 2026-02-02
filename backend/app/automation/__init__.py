"""
Module d'automatisation avec Playwright.
"""

from app.automation.base import BaseAutomation
from app.automation.vinted import VintedAutomation
from app.automation.leboncoin import LeboncoinAutomation

__all__ = [
    "BaseAutomation",
    "VintedAutomation", 
    "LeboncoinAutomation",
]
