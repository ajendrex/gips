import logging
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Generator, TypedDict, List, Tuple, Dict

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.utils.timezone import make_aware, is_aware

from informes.models import Prueba, Pregunta, Alternativa, Persona, Resultado, Respuesta
from informes.scanners.base import Scanner

BASE_URL = 'https://api.surveymonkey.com/v3'
UTC = ZoneInfo('UTC')
logger = logging.getLogger(__name__)


class SurveyMonkeyChoiceDict(TypedDict):
    id: str
    position: int
    text: str
    score: float


class SurveyMonkeyQuestionDict(TypedDict):
    page: int
    position: int
    id: str
    type: str
    text: str
    choices: List[SurveyMonkeyChoiceDict]


class SurveyMonkeyPruebaDict(TypedDict):
    title: str
    nickname: str
    date_created: str
    date_modified: str
    id: str
    href: str
    questions: List[SurveyMonkeyQuestionDict]


class ScannerSurveyMonkey(Scanner):
    PLATAFORMA = "SurveyMonkey"

    def _post_init(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {settings.SURVEY_MONKEY_API_KEY}',
            'Content-Type': 'application/json',
        })

    def _scan_nuevas_pruebas(self, from_dt: datetime) -> Generator[SurveyMonkeyPruebaDict, None, None]:
        url = f"{BASE_URL}/surveys"
        response = self.session.get(url, params={'start_modified_at': from_dt.isoformat(timespec="seconds")})

        yield from self._yield_paginated(response)

    def _yield_paginated(self, response: requests.Response) -> Generator[dict, None, None]:
        while True:
            data = response.json()

            for obj in data['data']:
                resp = self.session.get(obj['href'] + '/details')
                yield resp.json()

            new_page = data['links'].get('next')

            if new_page:
                response = self.session.get(new_page)
            else:
                break

    def _generate_questions_and_choices(
        self,
        prueba: Prueba,
        prueba_dict: dict,
    ) -> Generator[Tuple[Pregunta, List[Alternativa]], None, None]:
        for page in prueba_dict["pages"]:
            for question in page["questions"]:
                if question["family"] == "open_ended":
                    for row in question["answers"]["rows"]:
                        pregunta = Pregunta(
                            prueba=prueba,
                            pagina=page["position"],
                            posicion=question["position"],
                            tipo="open_ended",
                            plataforma=self.PLATAFORMA,
                            id_plataforma="_".join([question["id"], row["id"]]),
                            texto=row["text"],
                        )
                        yield pregunta, []
                else:
                    pregunta = Pregunta(
                        prueba=prueba,
                        pagina=page["position"],
                        posicion=question["position"],
                        tipo=question["family"],
                        plataforma=self.PLATAFORMA,
                        id_plataforma=question["id"],
                        texto=self._extract_text_from_html(question["headings"][0]["heading"]),
                    )
                    choices = [
                        Alternativa(
                            posicion=choice["position"],
                            id_plataforma=choice["id"],
                            texto=choice["text"],
                            puntaje=choice["score"],
                        )
                        for choice in self._get_choices_from_question(question)
                    ]
                    yield pregunta, choices

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

    @staticmethod
    def _get_choices_from_question(question: dict) -> List[SurveyMonkeyChoiceDict]:
        if question["family"] != "single_choice":
            return []

        choices = []

        for choice in question["answers"]["choices"]:
            choices.append({
                'id': choice["id"],
                'position': choice["position"],
                'text': choice["text"],
                'score': choice.get("quiz_options", {}).get("score", 0),
            })

        return choices

    @staticmethod
    def _str_to_datetime(date_str: str) -> datetime:
        dt = datetime.fromisoformat(date_str)

        return dt if is_aware(dt) else make_aware(dt, timezone=UTC)

    def _get_id_prueba(self, prueba_dict: dict) -> str:
        return prueba_dict['id']

    def _get_fecha_creacion_prueba(self, prueba_dict: dict) -> datetime:
        return self._str_to_datetime(prueba_dict['date_created'])

    def _get_fecha_actualizacion_prueba(self, prueba_dict: dict) -> datetime:
        return self._str_to_datetime(prueba_dict['date_modified'])

    def _get_nombre_prueba(self, prueba_dict: dict) -> str:
        return prueba_dict['title']

    def _scan_nuevas_respuestas(
            self,
            prueba: Prueba,
            from_dt: datetime,
    ) -> Generator[List[dict], None, None]:
        url = f"{BASE_URL}/surveys/{prueba.metadata['id']}/responses/bulk"
        response = self.session.get(url, params={'start_modified_at': from_dt.isoformat(timespec="seconds")})

        yield from self._yield_paginated(response)

    def _iter_respuestas(self, prueba: Prueba, resp: dict) -> Generator[Tuple[Pregunta, str, dict], None, None]:
        id_plataforma_to_pregunta = {
            pregunta.id_plataforma: pregunta
            for pregunta in Pregunta.objects.filter(prueba=prueba)
        }
        id_plataforma_to_alternativa = {
            alternativa.id_plataforma: alternativa
            for alternativa in Alternativa.objects.filter(pregunta__prueba=prueba)
        }

        for page in resp["pages"]:
            for question in page["questions"]:
                for answer in question["answers"]:
                    choice_id = answer.get("choice_id")

                    if choice_id:
                        alternativa = id_plataforma_to_alternativa[choice_id]
                        pregunta = id_plataforma_to_pregunta[question["id"]]

                        if alternativa.pregunta != pregunta:
                            raise ValueError(f"Alternativa {alternativa} no pertenece a la pregunta {pregunta}")

                        yield pregunta, alternativa, alternativa.texto, answer
                        continue

                    row_id = answer.get("row_id")
                    text = answer.get("text")

                    pregunta = id_plataforma_to_pregunta["_".join([question["id"], row_id])]
                    yield pregunta, None, text, answer

    def _build_persona(
        self,
        resultado: Resultado,
        resp: dict,
        id_plataforma_to_respuesta: Dict[str, Respuesta],
    ) -> Persona:
        persona = Persona()

        for campo, id_plataforma in resultado.prueba.parametros["campos_persona"].items():
            try:
                valor = id_plataforma_to_respuesta[id_plataforma].valor
            except KeyError:
                logger.info(f"No se encontró respuesta para el campo persona `{campo}`")
            else:
                setattr(persona, campo, valor)

        return persona

    def _get_id_resultado(self, resp: dict) -> str:
        return resp["id"]

    def _get_fecha_resultado(self, resp: dict) -> datetime:
        return self._str_to_datetime(resp["date_modified"])
