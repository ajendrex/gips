import random
import string
from abc import ABC, abstractmethod
from typing import Optional
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import HttpRequest

from informes.gips_service import GIPSService
from informes.models import Resultado


class Generador(ABC, GIPSService):
    def __init__(self, resultado: Resultado, request: Optional[HttpRequest]):
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

        self.resultado.clave_archivo, self.resultado.clave_acceso = self._generar_codigos()

        informe = self._generar_informe()
        informe_file = ContentFile(informe)
        django_file = File(informe_file, name=f"{self.resultado.clave_archivo}.pdf")

        self.resultado.informe = django_file
        self.resultado.save()

    def evaluar(self):
        try:
            if self.is_valid(raise_exception=True):
                self.resultado.evaluacion = self._evaluar()
        except Exception as e:
            self._add_error_message(f"Error al evaluar resultado: {e}")
        else:
            self.resultado.save()
            self._add_success_message("Resultado evaluado")

    @staticmethod
    def _generar_codigos(longitud_alfanumerico=12, longitud_numerico=5):
        # Generar código alfanumérico
        caracteres_alfanumericos = string.ascii_letters + string.digits
        codigo_alfanumerico = ''.join(random.choice(caracteres_alfanumericos) for _ in range(longitud_alfanumerico))

        # Generar código numérico
        codigo_numerico = ''.join(random.choice(string.digits) for _ in range(longitud_numerico))

        return codigo_alfanumerico, codigo_numerico

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
    def _evaluar(self) -> dict:
        ...

    @abstractmethod
    def _generar_informe(self) -> bytes:
        ...


def get_generador(resultado: Resultado, request: Optional[HttpRequest]) -> Optional[Generador]:
    from informes.generadores.puntaje_escala import GeneradorPuntajeEscala

    class_dict = {
        'GeneradorPuntajeEscala': GeneradorPuntajeEscala
    }

    try:
        return class_dict[resultado.prueba.algoritmo_evaluacion.clase](resultado, request)
    except (AttributeError, KeyError):
        return None
