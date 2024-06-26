from abc import ABC, abstractmethod
from typing import Optional, Tuple

import qrcode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import HttpRequest

from tests.gips_service import GIPSService
from tests.models import Resultado, ResultadoEvaluacion
from utils.text import numerico_random

LONGITUD_CLAVE_ARCHIVO = 5


class Generador(ABC, GIPSService):
    def __init__(self, resultado: Optional[Resultado], request: Optional[HttpRequest]):
        self.resultado = resultado
        super().__init__(request=request)

    def is_valid(self, raise_exception: bool = False) -> bool:
        try:
            self._validate()
        except ValidationError as err:
            if raise_exception:
                raise
            self._add_error_message(f"No se puede evaluar: {err}")
            return False

        return True

    @abstractmethod
    def _validate(self):
        ...

    def generar(self):
        """
        Genera el informe en formato pdf y lo devuelve como un objeto File.
        Almacena en self.resultado.evaluacion el registro de los puntajes calculados.
        """
        try:
            self.puede_generar_informe(raise_exception=True)
        except ValidationError as e:
            self._add_error_message(f"Error al generar informe: {e}")
            return

        self.resultado.clave_archivo = numerico_random(LONGITUD_CLAVE_ARCHIVO)

        qr_image = self._generar_qr(self.resultado.acceso.codigo)

        informe = self._generar_informe(qr_image)
        informe_file = ContentFile(informe)
        django_file = File(informe_file, name=f"{self.resultado.acceso.codigo}.pdf")

        self.resultado.informe = django_file
        self.resultado.save()

        self._add_success_message("Informe generado")

    @abstractmethod
    def generar_html_evaluacion(self) -> str:
        ...

    @staticmethod
    def _generar_qr(codigo: str) -> bytes:
        url = f"{settings.BASE_URL}/verificar/{codigo}"
        return qrcode.make(
            url,
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=0,
        )

    def evaluar(self):
        try:
            if self.is_valid(raise_exception=True):
                evaluacion, resultado_evaluacion = self._evaluar()
                self.resultado.evaluacion = evaluacion
                self.resultado.resultado_test = resultado_evaluacion
        except Exception as e:
            self._add_error_message(f"Error al evaluar test: {e}")
        else:
            self.resultado.save()

            entrevista = self.resultado.entrevista

            if not entrevista.observaciones and self.resultado.evaluacion:
                entrevista.observaciones = entrevista.resultado.evaluacion.get("observaciones_initial", "")
                entrevista.save()

            self._add_success_message("Test evaluado")

    def puede_generar_informe(self, raise_exception: bool = False) -> bool:
        try:
            self._validar_puede_generar_informe()
        except ValidationError as err:
            if raise_exception:
                raise
            self._add_error_message(f"No se puede generar informe: {err}")
            return False

        return True

    @abstractmethod
    def _validar_puede_generar_informe(self):
        ...

    @abstractmethod
    def _evaluar(self) -> Tuple[dict, ResultadoEvaluacion]:
        ...

    @abstractmethod
    def _generar_informe(self, qr_image: bytes) -> bytes:
        ...


def get_generador(resultado: Optional[Resultado], request: Optional[HttpRequest] = None) -> Optional[Generador]:
    from tests.generadores.puntaje_escala import GeneradorPuntajeEscala

    if resultado:
        return GeneradorPuntajeEscala(resultado, request)
