

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List

from babel.dates import format_date
from django.db import transaction
from django.http import JsonResponse
from django.utils.timezone import make_aware
from rest_framework.decorators import api_view
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from entrevistas.ghd import HorarioGlobal, MINUTOS_BLOQUE_ENTREVISTA, BloqueHorario, HORA_FMT
from entrevistas.models import TZ_CHILE, Entrevista, Entrevistador
from entrevistas.serializers import EntrevistaSerializer
from tests.models import AccesoTestPersona
from utils.numbers import obtener_numero_aleatorio
from utils.request import get_and_validate_acceso


class EntrevistadorConEntrevistasException(Exception):
    pass


def horarios_disponibles(request):
    try:
        get_and_validate_acceso(request)
    except AuthenticationFailed:
        return JsonResponse({"error": "No parece que tengas acceso a un test."}, status=401)
    except ValidationError:
        return JsonResponse({"error": "Ya has completado este test."}, status=400)

    ahora = datetime.now(tz=TZ_CHILE)
    manhana = datetime(ahora.year, ahora.month, ahora.day, 10, tzinfo=TZ_CHILE) + timedelta(days=1)
    horarios = HorarioGlobal().generar_bloques_disponibles(
        fecha_inicio=manhana,
        fecha_fin=ahora + timedelta(days=8),
    )
    horarios_dict = defaultdict(list)

    for h in horarios:
        horarios_dict[h.inicio.date()].append(h)

    return JsonResponse({
        "dias": [
            {
                "fecha": _format_fecha(fecha),
                "bloques": [bloque.to_dict() for bloque in _split_bloques(bloques)],
            }
            for fecha, bloques in horarios_dict.items()
        ]
    })


def _format_fecha(fecha: date) -> str:
    texto_fecha = format_date(fecha, "EEEE d 'de' MMMM", locale='es_ES')
    parts = texto_fecha.split(" ")
    return f"{parts[0].capitalize()}|{parts[1]} de {parts[3].capitalize()}"


def _split_bloques(bloques: List[BloqueHorario]) -> List[BloqueHorario]:
    bloques_separados = []

    for bloque in bloques:
        inicio = bloque.inicio
        fin = bloque.fin

        while inicio < fin:
            nuevo_fin = inicio + timedelta(minutes=MINUTOS_BLOQUE_ENTREVISTA)

            if nuevo_fin > fin:
                return bloques_separados

            bloques_separados.append(BloqueHorario(inicio, nuevo_fin))
            inicio = nuevo_fin

    return bloques_separados


@api_view(['POST'])  # decodifica request.body y escribe en request.data
def crear_entrevista(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        acceso = get_and_validate_acceso(request)
    except AuthenticationFailed:
        return JsonResponse({"error": "No parece que tengas acceso a un test."}, status=401)
    except ValidationError:
        return JsonResponse({"error": "Ya has completado este test."}, status=400)

    inicio = datetime.strptime(request.data["fecha"], HORA_FMT)
    inicio = make_aware(inicio, TZ_CHILE)
    ahora = datetime.now(tz=TZ_CHILE)

    if inicio < ahora + timedelta(hours=16):
        return JsonResponse(
            {"error": "No puedes programar una entrevista para antes de 16 horas desde ahora"},
            status=400,
        )

    termino = inicio + timedelta(minutes=int(MINUTOS_BLOQUE_ENTREVISTA))

    for _ in range(2):
        entrevistadores = HorarioGlobal().obtener_entrevistadores(inicio, termino)

        if not entrevistadores:
            return JsonResponse({"error": "No hay sicólogos disponibles en ese horario"}, status=400)

        entrevistador = entrevistadores[obtener_numero_aleatorio(0, len(entrevistadores) - 1)]

        try:
            entrevista = _safe_crear_entrevista(entrevistador.id, inicio, termino, acceso.id)
        except ValueError as err:
            return JsonResponse({"error": str(err)}, status=400)
        except EntrevistadorConEntrevistasException:
            pass
        else:
            return JsonResponse({
                "mensaje": "Entrevista creada",
                "entrevista": EntrevistaSerializer(entrevista).data,
            }, status=201)

    return JsonResponse({"error": "No se pudo crear la entrevista"}, status=500)


def _safe_crear_entrevista(entrevistador_id: int, inicio: datetime, termino: datetime, acceso_id: int) -> Entrevista:
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
        return Entrevista.objects.create(
            entrevistador=entrevistador,
            fecha_inicio=inicio,
            fecha_fin=termino,
            acceso=acceso,
        )
