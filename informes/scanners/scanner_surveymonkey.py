from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Generator, TypedDict, List

import requests

from django.conf import settings
from django.utils.timezone import make_aware

from informes.models import Prueba, Pregunta, Alternativa
from informes.scanners.base import Scanner

BASE_URL = 'https://api.surveymonkey.com/v3'
UTC = ZoneInfo('UTC')


class SurveyMonkeyChoiceDict(TypedDict):
    id: str
    position: int
    text: str
    score: float


class SurveyMonkeyQuestionDict(TypedDict):
    page: int
    position: int
    id: str
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
                yield self._get_prueba_dict(obj)

            new_page = data['links'].get('next')

            if new_page:
                response = self.session.get(new_page)
            else:
                break

    def _get_prueba_dict(self, obj: dict) -> SurveyMonkeyPruebaDict:
        resp = self.session.get(obj["href"] + "/details")
        data = resp.json()
        return {
            'title': data['title'],
            'nickname': data['nickname'],
            'date_created': data['date_created'],
            'date_modified': data['date_modified'],
            'id': data['id'],
            'href': data['href'],
            'questions': self._get_questions_from_survey_pages(data["pages"])
        }

    def _get_questions_from_survey_pages(self, pages: List[dict]) -> List[SurveyMonkeyQuestionDict]:
        questions = []
        for page in pages:
            for question in page["questions"]:
                questions.append({
                    'page': page["position"],
                    'position': question["position"],
                    'id': question["id"],
                    'text': question["headings"][0]["heading"],
                    'choices': self._get_choices_from_question(question)
                })
        return questions

    @staticmethod
    def _get_choices_from_question(question: dict) -> List[SurveyMonkeyChoiceDict]:
        if question["family"] != "single_choice":
            return []

        choices = []
        answers = question["answers"]

        for choice in answers["choices"]:
            choices.append({
                'id': choice["id"],
                'position': choice["position"],
                'text': choice["text"],
                'score': choice.get("quiz_options", {}).get("score", 0),
            })

        return choices

    def _create_prueba(self, prueba_dict: SurveyMonkeyPruebaDict) -> Prueba:
        prueba = Prueba.objects.create(
            nombre=prueba_dict['title'],
            plataforma='SurveyMonkey',
            fecha_creacion=self._str_to_datetime(prueba_dict['date_created']),
            fecha_actualizacion=self._str_to_datetime(prueba_dict['date_modified']),
            metadata=prueba_dict,
        )

        preguntas = []

        for question in prueba_dict['questions']:
            preguntas.append(
                Pregunta(
                    prueba=prueba,
                    pagina=question['page'],
                    posicion=question['position'],
                    id_externo=question['id'],
                    texto=question['text'],
                )
            )

        id_externo_to_pregunta = {
            pregunta.id_externo: pregunta
            for pregunta in Pregunta.objects.bulk_create(preguntas)
        }

        alternativas = []

        for question in prueba_dict['questions']:
            pregunta = id_externo_to_pregunta[question['id']]

            for choice in question['choices']:
                alternativas.append(
                    Alternativa(
                        pregunta=pregunta,
                        posicion=choice['position'],
                        id_externo=choice['id'],
                        texto=choice['text'],
                        puntaje=choice['score'],
                    )
                )

        Alternativa.objects.bulk_create(alternativas)

        return prueba

    @staticmethod
    def _str_to_datetime(date_str: str) -> datetime:
        return make_aware(datetime.fromisoformat(date_str), timezone=UTC)

    def _scan_nuevas_respuestas(
            self,
            prueba: Prueba,
            from_dt: datetime,
    ) -> Generator[List[dict], None, None]:
        raise NotImplementedError

    def _create_resultado(self, prueba, resp):
        raise NotImplementedError
