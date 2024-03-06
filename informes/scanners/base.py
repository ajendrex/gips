from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generator, Tuple, List

from django.contrib import messages
from django.http import HttpRequest

from informes.models import Prueba, Resultado


class Scanner(ABC):
    def __init__(self, request: HttpRequest):
        self.request = request
        self._post_init()

    def _post_init(self):
        pass

    def scan_pruebas(self, from_dt: datetime) -> Tuple[List[Prueba], List[Tuple[dict, Exception]]]:
        pruebas = []
        errores = []

        for prueba_dict in self._scan_nuevas_pruebas(from_dt):
            try:
                pruebas.append(self._create_prueba(prueba_dict))
            except Exception as e:
                errores.append((prueba_dict, e))

        return pruebas, errores

    def scan_respuestas(self, prueba: Prueba) -> Tuple[List[Resultado], List[Tuple[dict, Exception]]]:
        from_dt = prueba.resultados.latest('fecha').fecha
        resultados = []
        errores = []

        for resp in self._scan_nuevas_respuestas(prueba, from_dt):
            try:
                resultados.append(self._create_resultado(prueba, resp))
            except Exception as e:
                errores.append((resp, e))

        return resultados, errores

    @abstractmethod
    def _scan_nuevas_pruebas(self, from_dt: datetime) -> Generator[dict, None, None]:
        ...

    @abstractmethod
    def _create_prueba(self, prueba_dict):
        ...

    @abstractmethod
    def _scan_nuevas_respuestas(self, prueba: Prueba, from_dt: datetime) -> Generator[dict, None, None]:
        ...

    @abstractmethod
    def _create_resultado(self, prueba: Prueba, resp: dict) -> Resultado:
        ...

    def _add_error_message(self, message: str):
        messages.error(self.request, message)
