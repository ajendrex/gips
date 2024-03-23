import random
import string


def alfanumerico_random(longitud: int) -> str:
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))


def numerico_random(longitud: int) -> str:
    return ''.join(random.choice(string.digits) for _ in range(longitud))
