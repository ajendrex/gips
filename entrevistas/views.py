from datetime import datetime, timedelta

from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from entrevistas.ghd import HorarioGlobal, MINUTOS_BLOQUE_ENTREVISTA
from entrevistas.models import TZ_CHILE, Entrevista
from tests.models import AccesoTestPersona
from utils.numbers import obtener_numero_aleatorio


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

    entrevistadores = HorarioGlobal().obtener_entrevistadores(inicio, termino)

    if not entrevistadores:
        return JsonResponse({"error": "No hay entrevistadores disponibles en ese horario"}, status=400)

    entrevistador = entrevistadores[obtener_numero_aleatorio(0, len(entrevistadores) - 1)]

    Entrevista.objects
