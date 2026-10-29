"""Turns ParaBank money text such as "$1,515.50" or "-$10.00" into a Decimal."""
from decimal import Decimal


def parse_money(text: str) -> Decimal:
    cleaned = text.strip().replace("$", "").replace(",", "")
    return Decimal(cleaned)
