import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generator, Tuple, List, Optional, Dict

import reversion
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest

from informes.gips_service import GIPSService
from informes.models import Prueba, Resultado, Persona, Pregunta, Alternativa, Respuesta

logger = logging.getLogger(__name__)


class Scanner(ABC, GIPSService):
    PLATAFORMA: str

    def __init__(self, request: Optional[HttpRequest] = None):
        super().__init__(request=request)
        self._post_init()

    def _post_init(self):
        pass

    def scan(self):
        pruebas, errores = self.scan_pruebas()

        for prueba in pruebas:
            self._add_success_message(f"Se ha descargado la prueba {prueba}")

        for error in errores:
            self._add_error_message(f"Error al descargar prueba: {error[1]}")

        for prueba in Prueba.objects.filter(plataforma=self.PLATAFORMA, parametros__isnull=False):
            resultados, errores = self.scan_respuestas(prueba)

            logger.info(f"Descargados {len(resultados)} resultados para la prueba {prueba}")

            if errores:
                logger.error(f"Errores al descargar resultados para la prueba {prueba}")
                for resp, e in errores:
                    logger.error(f"Error en respuesta {resp}: {e}")

    def scan_pruebas(self) -> Tuple[List[Prueba], List[Tuple[dict, Exception]]]:
        pruebas = []
        errores = []

        last_prueba = Prueba.objects.order_by('-fecha_actualizacion').first()
        from_dt = last_prueba.fecha_actualizacion if last_prueba else datetime(2012, 12, 12)

        for prueba_dict in self._scan_nuevas_pruebas(from_dt):
            try:
                pruebas.append(self._create_prueba(prueba_dict))
            except Exception as e:
                logger.error(
                    f"Error al crear prueba: {e}",
                    exc_info=True,
                    stack_info=True,
                )
                errores.append((prueba_dict, e))

        if pruebas:
            self._add_success_message(f"Se han descargado {len(pruebas)} pruebas")
        if errores:
            self._add_error_message(f"Se han producido {len(errores)} errores al descargar pruebas")

        return pruebas, errores

    def scan_respuestas(self, prueba: Prueba) -> Tuple[List[Resultado], List[Tuple[dict, Exception]]]:
        last_resultado = prueba.resultados.order_by('-fecha').first()
        from_dt = last_resultado.fecha if last_resultado else datetime(2012, 12, 12)
        resultados = []
        errores = []

        for resp in self._scan_nuevas_respuestas(prueba, from_dt):
            try:
                with transaction.atomic():
                    resultados.append(self._parse_respuesta(prueba, resp))
            except Exception as e:
                errores.append((resp, e))

        if resultados:
            self._add_success_message(f"Se han descargado {len(resultados)} respuestas")
        if errores:
            self._add_error_message(f"Se han producido {len(errores)} errores al descargar respuestas")

        return resultados, errores

    @abstractmethod
    def _scan_nuevas_pruebas(self, from_dt: datetime) -> Generator[dict, None, None]:
        ...

    def _create_prueba(self, prueba_dict) -> Prueba:
        with transaction.atomic():
            prueba = Prueba.objects.create(
                plataforma=self.PLATAFORMA,
                id_plataforma=self._get_id_prueba(prueba_dict),
                fecha_creacion=self._get_fecha_creacion_prueba(prueba_dict),
                fecha_actualizacion=self._get_fecha_actualizacion_prueba(prueba_dict),
                nombre=self._get_nombre_prueba(prueba_dict),
                metadata=prueba_dict,
            )

            for pregunta, alternativas in self._generate_questions_and_choices(prueba, prueba_dict):
                pregunta.save()

                for alternativa in alternativas:
                    alternativa.pregunta = pregunta

                Alternativa.objects.bulk_create(alternativas)

            return prueba

    @abstractmethod
    def _get_id_prueba(self, prueba_dict: dict) -> str:
        ...

    @abstractmethod
    def _get_fecha_creacion_prueba(self, prueba_dict: dict) -> datetime:
        ...

    @abstractmethod
    def _get_fecha_actualizacion_prueba(self, prueba_dict: dict) -> datetime:
        ...

    @abstractmethod
    def _get_nombre_prueba(self, prueba_dict: dict) -> str:
        ...

    @abstractmethod
    def _scan_nuevas_respuestas(self, prueba: Prueba, from_dt: datetime) -> Generator[dict, None, None]:
        ...

    def _parse_respuesta(self, prueba: Prueba, resp: dict) -> Resultado:
        resultado = Resultado.objects.create(
            prueba=prueba,
            id_plataforma=self._get_id_resultado(resp),
            fecha=self._get_fecha_resultado(resp),
            metadata=resp,
        )

        respuestas_to_create = []

        for pregunta, alternativa, valor, metadata in self._iter_respuestas(prueba, resp):
            respuestas_to_create.append(
                Respuesta(
                    resultado=resultado,
                    pregunta=pregunta,
                    alternativa=alternativa,
                    valor=valor.strip(),
                    metadata=metadata,
                )
            )

        Respuesta.objects.bulk_create(respuestas_to_create)

        try:
            persona, created, updated = self._update_or_create_persona(resultado, resp)
        except Exception as e:
            self._add_error_message(f"Error al crear persona para resultado {resultado}: {e}")
        else:
            if created:
                logger.info(f"Persona {persona} creada para resultado {resultado}")
            elif updated:
                logger.info(f"Persona {persona} actualizada para resultado {resultado}")
            resultado.persona = persona
            resultado.save()

        return resultado

    @abstractmethod
    def _iter_respuestas(
        self,
        prueba: Prueba,
        resp: dict,
    ) -> Generator[Tuple[Pregunta, Optional[Alternativa], str, dict], None, None]:
        ...

    @abstractmethod
    def _generate_questions_and_choices(
        self,
        prueba: Prueba,
        prueba_dict: dict,
    ) -> Generator[Tuple[Pregunta, List[Alternativa]], None, None]:
        ...

    @abstractmethod
    def _get_id_resultado(self, resp: dict) -> str:
        ...

    @abstractmethod
    def _get_fecha_resultado(self, resp: dict) -> datetime:
        ...

    def _update_or_create_persona(self, resultado: Resultado, resp: dict) -> Tuple[Persona, bool, bool]:
        id_plataforma_to_respuesta = {
            respuesta.pregunta.id_plataforma: respuesta
            for respuesta in resultado.respuestas.all()
        }
        persona_obj = self._build_persona(resultado, resp, id_plataforma_to_respuesta)

        cleaned_rut = re.sub(r'[^0-9kK]', '', persona_obj.rut)

        if not cleaned_rut:
            raise ValueError(f"RUT vacío para resultado {resultado}")

        with reversion.create_revision():
            defaults = {
                'nombres': persona_obj.nombres,
                'apellido_paterno': persona_obj.apellido_paterno,
                'apellido_materno': persona_obj.apellido_materno or "",
                'email': persona_obj.email or "",
                'nacionalidad': persona_obj.nacionalidad or "",
                'fecha_nacimiento': persona_obj.fecha_nacimiento,
            }
            persona, created = Persona.objects.get_or_create(rut=cleaned_rut, defaults=defaults)
            updated = False

            if not created:
                for field, value in defaults.items():
                    if getattr(persona, field) != value:
                        updated = True
                        setattr(persona, field, value)

                if updated:
                    persona.save()

        return persona, created, updated

    @abstractmethod
    def _build_persona(
        self,
        resultado: Resultado,
        resp: dict,
        id_plataforma_to_respuesta: Dict[str, Respuesta],
    ) -> Persona:
        ...
