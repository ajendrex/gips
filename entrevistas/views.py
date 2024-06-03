

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List

from babel.dates import format_date
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve
from rest_framework.decorators import api_view
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from entrevistas.ghd import HorarioGlobal, MINUTOS_BLOQUE_ENTREVISTA, BloqueHorario, HORA_FMT
from entrevistas.models import Entrevista, Sicologo
from entrevistas.serializers import EntrevistaSerializer
from tests.models import AccesoTestPersona, Resultado
from utils.fechas import TZ_CHILE
from utils.numbers import obtener_numero_aleatorio
from utils.request import get_and_validate_acceso


class EntrevistadorConEntrevistasException(Exception):
    pass


@csrf_exempt
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


@csrf_exempt
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
    manhana = datetime(ahora.year, ahora.month, ahora.day, 10, tzinfo=TZ_CHILE) + timedelta(days=1)
    if inicio < manhana:
        return JsonResponse(
            {"error": "Hora de inicio no puede ser antes de las 10:00 AM del día siguiente"},
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
        entrevistador = Sicologo.objects.select_for_update().get(pk=entrevistador_id)

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
            resultado=acceso.resultado,
        )


@csrf_exempt
def verificar(request, clave_acceso):
    if request.method == "POST":
        clave_archivo = request.POST.get("clave_archivo")

        try:
            resultado = Resultado.objects.get(clave_archivo=clave_archivo, acceso__codigo=clave_acceso)
        except Resultado.DoesNotExist:
            return render(request, "entrevistas/no_verificado.html", {"clave_archivo": clave_archivo})

        # responder el contenido del informe
        try:
            with resultado.informe.open('rb') as pdf:
                # Leer el contenido del archivo
                pdf_content = pdf.read()

                # Crear una respuesta HTTP con el contenido del PDF
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="%s"' % resultado.informe.name

                return response
        except Exception as e:
            # Manejar el error o devolver una respuesta de error
            return render(request, "entrevistas/error_verificacion.html")

    return render(request, "entrevistas/verificar.html")


@login_required
def serve_protected_media(request, path):
    """
    Sirve los archivos de media con protección basada en autenticación.
    """
    document_root = settings.MEDIA_ROOT
    return serve(request, path, document_root=document_root)
