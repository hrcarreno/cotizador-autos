"""
Generador del código disfrazado.
El código codifica el descuento comercial en un formato alfanumérico
que el cliente NO puede interpretar.

Formato: [LL][MMM][LL][DDD][LL][CCC]
- LL  = 2 letras aleatorias (disfraz)
- MMM = millones del monto (3 dígitos)
- DDD = miles del monto (3 dígitos)
- CCC = cientos del monto (3 dígitos)

Ejemplo: descuento $12.231.971 → "FC012HC231AC971"
Ejemplo: descuento $512.082    → "KJ000ER512WM082"
"""

import random
import string


def _dos_letras_random():
    """Genera 2 letras mayúsculas aleatorias."""
    return "".join(random.choices(string.ascii_uppercase, k=2))


def generar_codigo_disfrazado(monto):
    """
    Genera el código disfrazado a partir del monto de descuento.
    Si el monto es 0 o negativo, devuelve cadena vacía.
    """
    if monto is None or monto <= 0:
        return ""

    monto = int(round(monto))

    millones = monto // 1_000_000
    miles = (monto // 1_000) % 1_000
    cientos = monto % 1_000

    return (
        f"{_dos_letras_random()}{millones:03d}"
        f"{_dos_letras_random()}{miles:03d}"
        f"{_dos_letras_random()}{cientos:03d}"
    )


def descomponer_codigo(codigo):
    """
    Función inversa: a partir de un código, devuelve el monto.
    Útil para debug o para validar.
    """
    if not codigo or len(codigo) != 14:
        return None

    try:
        millones = int(codigo[2:5])
        miles = int(codigo[7:10])
        cientos = int(codigo[12:15]) if len(codigo) >= 15 else int(codigo[12:])
        return millones * 1_000_000 + miles * 1_000 + cientos
    except (ValueError, IndexError):
        return None
