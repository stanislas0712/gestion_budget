from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide(value, arg):
    """Divise value par arg et retourne le résultat"""
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('1')
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplie value par arg et retourne le résultat"""
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('0')
        return value * arg
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calcule le pourcentage de value par rapport à total"""
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        total = Decimal(str(total)) if total else Decimal('1')
        if total == 0:
            return 0
        return (value / total) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
