import random


def obtener_numero_aleatorio(n, m):
    """
    Genera un número aleatorio entre n y m, ambos incluidos.

    Parámetros:
    n (int): Límite inferior del rango (debe ser positivo).
    m (int): Límite superior del rango (debe ser positivo y mayor o igual que n).

    Retorna:
    int: Un número aleatorio entre n y m.
    """
    if n > m:
        raise ValueError("n debe ser menor o igual que m")
    if n < 0 or m < 0:
        raise ValueError("n y m deben ser números enteros positivos")
    return random.randint(n, m)
