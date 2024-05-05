from rest_framework.exceptions import AuthenticationFailed, ValidationError

from tests.models import AccesoTestPersona


def get_and_validate_acceso(request) -> AccesoTestPersona:
    try:
        acceso = AccesoTestPersona.objects.get(codigo=request.GET.get('codigo'))
    except AccesoTestPersona.DoesNotExist:
        raise AuthenticationFailed("No parece que tengas acceso a un test.")

    if acceso.entrevistas.exists():
        raise ValidationError("Ya has completado este test.")

    return acceso
