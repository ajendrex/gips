from datetime import datetime, timedelta

from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from entrevistas.ghd import HorarioGlobal
from entrevistas.models import TZ_CHILE
from tests.models import AccesoTestPersona


def _validate_request(request):
    if not AccesoTestPersona.objects.filter(codigo=request.GET.get('codigo')).exists():
        raise AuthenticationFailed("No parece que tengas acceso a un test.")


def horarios_disponibles(request):
    _validate_request(request)
    ahora = datetime.now(tz=TZ_CHILE)
    horarios = HorarioGlobal().generar_bloques_disponibles(
        fecha_inicio=ahora + timedelta(days=1),
        fecha_fin=ahora + timedelta(days=15),
    )
    return JsonResponse({"horarios": [h.to_dict() for h in horarios]})


def crear_entrevista(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    _validate_request(request)

    data = request.POST
    inicio = datetime.strptime(data["fecha"], "%Y-%m-%d %H:%M")
    termino = inicio + timedelta(minutes=int(MINUTOS_BLOQUE_ENTREVISTA))
