"""
Generador del código disfrazado.
Estructura: [LL][MMM][LL][DDD][LL][CCC] = 15 caracteres.
"""

import random
import string


def _dos_letras_random():
    return "".join(random.choices(string.ascii_uppercase, k=2))


def generar_codigo_disfrazado(monto):
    """
    Genera el código disfrazado a partir del monto de descuento.
    """
    if monto is None or monto <= 0:
        return ""

    monto = int(round(monto))
    millones = monto // 1_000_000
    miles = (monto // 1_000) % 1_000
    cientos = monto % 1_000

    l1 = _dos_letras_random()
    l2 = _dos_letras_random()
    l3 = _dos_letras_random()

    return f"{l1}{str(millones).zfill(3)}{l2}{str(miles).zfill(3)}{l3}{str(cientos).zfill(3)}"


def descomponer_codigo(codigo):
    """Función inversa: código → monto."""
    if not codigo or len(codigo) != 15:
        return None
    try:
        millones = int(codigo[2:5])
        miles = int(codigo[7:10])
        cientos = int(codigo[12:15])
        return millones * 1_000_000 + miles * 1_000 + cientos
    except (ValueError, IndexError):
        return None
