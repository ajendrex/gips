from collections import defaultdict
from datetime import datetime, timedelta

from django.db import transaction
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from entrevistas.ghd import HorarioGlobal, MINUTOS_BLOQUE_ENTREVISTA
from entrevistas.models import TZ_CHILE, Entrevista, Entrevistador
from tests.models import AccesoTestPersona
from utils.numbers import obtener_numero_aleatorio


class EntrevistadorConEntrevistasException(Exception):
    pass


def _validate_request(request) -> AccesoTestPersona:
    try:
        return AccesoTestPersona.objects.get(codigo=request.GET.get('codigo'))
    except AccesoTestPersona.DoesNotExist:
        raise AuthenticationFailed("No parece que tengas acceso a un test.")


def horarios_disponibles(request):
    _validate_request(request)
    ahora = datetime.now(tz=TZ_CHILE)
    horarios = HorarioGlobal().generar_bloques_disponibles(
        fecha_inicio=ahora + timedelta(days=1),
        fecha_fin=ahora + timedelta(days=8),
    )
    horarios_dict = defaultdict(list)

    for h in horarios:
        horarios_dict[h.inicio.date()].append(h)

    return JsonResponse({
        "dias": [
            {
                "fecha": str(fecha),
                "bloques": [bloque.to_dict() for bloque in bloques],
            }
            for fecha, bloques in horarios_dict.items()
        ]
    })


def crear_entrevista(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    acceso = _validate_request(request)

    data = request.POST
    inicio = datetime.strptime(data["fecha"], "%Y-%m-%d %H:%M")
    termino = inicio + timedelta(minutes=int(MINUTOS_BLOQUE_ENTREVISTA))

    for _ in range(2):
        entrevistadores = HorarioGlobal().obtener_entrevistadores(inicio, termino)

        if not entrevistadores:
            return JsonResponse({"error": "No hay sicólogos disponibles en ese horario"}, status=400)

        entrevistador = entrevistadores[obtener_numero_aleatorio(0, len(entrevistadores) - 1)]

        try:
            _safe_crear_entrevista(entrevistador.id, inicio, termino, acceso.id)
        except ValueError as err:
            return JsonResponse({"error": str(err)}, status=400)
        except EntrevistadorConEntrevistasException:
            pass
        else:
            return JsonResponse({"mensaje": "Entrevista creada"}, status=201)

    return JsonResponse({"error": "No se pudo crear la entrevista"}, status=500)


def _safe_crear_entrevista(entrevistador_id: int, inicio: datetime, termino: datetime, acceso_id: int):
    with transaction.atomic():
        # Obtener el entrevistador y bloquearlo
        entrevistador = Entrevistador.objects.select_for_update().get(pk=entrevistador_id)

        # Verificar solapamientos
        if entrevistador.entrevistas.filter(fecha_inicio__lt=termino, fecha_fin__gt=inicio).exists():
            raise EntrevistadorConEntrevistasException()

        acceso = AccesoTestPersona.objects.select_for_update().get(pk=acceso_id)

        if acceso.entrevistas.exists():
            raise ValueError("Ya tienes una entrevista programada")

        # Crear la entrevista
        Entrevista.objects.create(
            entrevistador=entrevistador,
            entrevistado_id=acceso.persona_id,
            fecha_inicio=inicio,
            fecha_fin=termino,
            acceso=acceso,
        )
