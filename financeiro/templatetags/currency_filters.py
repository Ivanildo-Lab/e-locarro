from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def br_currency(value):
    """Formata valor como moeda brasileira: R$ 100.000,00"""
    try:
        valor = float(value)
        parte_inteira = int(abs(valor))
        parte_decimal = int(round((abs(valor) - parte_inteira) * 100))

        s = str(parte_inteira)
        resultado = ""
        for i, c in enumerate(reversed(s)):
            if i and i % 3 == 0:
                resultado = "." + resultado
            resultado = c + resultado

        return mark_safe(f"R$ {resultado},{parte_decimal:02d}")
    except (ValueError, TypeError):
        return f"R$ {value}"
