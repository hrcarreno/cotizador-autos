def generar_codigo_disfrazado(monto):
    """
    Genera el código disfrazado a partir del monto de descuento.
    Estructura: [LL][MMM][LL][DDD][LL][CCC] = 15 caracteres.
    """
    if monto is None or monto <= 0:
        return ""

    monto = int(round(monto))

    millones = monto // 1_000_000
    miles = (monto // 1_000) % 1_000
    cientos = monto % 1_000

    # Generar las 6 letras aleatorias
    l1 = _dos_letras_random()
    l2 = _dos_letras_random()
    l3 = _dos_letras_random()

    # Formatear números a 3 dígitos con ceros a la izquierda
    mmm = str(millones).zfill(3)
    ddd = str(miles).zfill(3)
    ccc = str(cientos).zfill(3)

    return f"{l1}{mmm}{l2}{ddd}{l3}{ccc}"
