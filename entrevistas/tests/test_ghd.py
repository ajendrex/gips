from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import User

from entrevistas.ghd import Horario
from entrevistas.models import TZ_CHILE


@pytest.mark.django_db
class TestGeneradorDeHorasDeDisponibilidad:
    def test_gdh_sin_bloqueos(self):
        entrevistador = User.objects.create_user(username="entrevistador")
        horario = Horario(entrevistador)
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=14,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 2
        assert bloques[0].inicio == datetime(2024, 4, 1, 8, 0, tzinfo=TZ_CHILE)
        assert bloques[0].fin == datetime(2024, 4, 1, 12, 0, tzinfo=TZ_CHILE)
        assert bloques[1].inicio == datetime(2024, 4, 1, 14, 0, tzinfo=TZ_CHILE)
        assert bloques[1].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

    def test_gdh_con_bloqueos(self):
        entrevistador = User.objects.create_user(username="entrevistador")
        horario = Horario(entrevistador)
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=14,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )
        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 1, 10, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 1, 11, 0, tzinfo=TZ_CHILE),
        )
        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 1, 15, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 1, 16, 0, tzinfo=TZ_CHILE),
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 4
        assert bloques[0].inicio == datetime(2024, 4, 1, 8, 0, tzinfo=TZ_CHILE)
        assert bloques[0].fin == datetime(2024, 4, 1, 10, 0, tzinfo=TZ_CHILE)
        assert bloques[1].inicio == datetime(2024, 4, 1, 11, 0, tzinfo=TZ_CHILE)
        assert bloques[1].fin == datetime(2024, 4, 1, 12, 0, tzinfo=TZ_CHILE)
        assert bloques[2].inicio == datetime(2024, 4, 1, 14, 0, tzinfo=TZ_CHILE)
        assert bloques[2].fin == datetime(2024, 4, 1, 15, 0, tzinfo=TZ_CHILE)
        assert bloques[3].inicio == datetime(2024, 4, 1, 16, 0, tzinfo=TZ_CHILE)
        assert bloques[3].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

    def test_gdh_bloqueo_total(self):
        entrevistador = User.objects.create_user(username="entrevistador")
        horario = Horario(entrevistador)
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=14,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )
        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 1, 7, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 1, 13, 0, tzinfo=TZ_CHILE),
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 1

        assert bloques[0].inicio == datetime(2024, 4, 1, 14, 0, tzinfo=TZ_CHILE)
        assert bloques[0].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 1, 14, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 1, 18, tzinfo=TZ_CHILE),
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 0

    def test_gdh_entre_dias(self):
        entrevistador = User.objects.create_user(username="entrevistador")
        horario = Horario(entrevistador)

        for dia in ["lunes", "martes", "miercoles"]:
            entrevistador.horarios_disponibles.create(
                dia=dia,
                hora_inicio=8,
                minuto_inicio=0,
                hora_fin=12,
                minuto_fin=0,
            )
            entrevistador.horarios_disponibles.create(
                dia=dia,
                hora_inicio=14,
                minuto_inicio=0,
                hora_fin=18,
                minuto_fin=0,
            )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 6

        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 1, 16, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 2, 16, 0, tzinfo=TZ_CHILE),
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 5
        assert bloques[1].fin == datetime(2024, 4, 1, 16, 0, tzinfo=TZ_CHILE)
        assert bloques[2].inicio == datetime(2024, 4, 2, 16, 0, tzinfo=TZ_CHILE)

        entrevistador.bloqueos.create(
            fecha_inicio=datetime(2024, 4, 2, 17, 0, tzinfo=TZ_CHILE),
            fecha_fin=datetime(2024, 4, 3, 12, 0, tzinfo=TZ_CHILE),
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 4
        assert bloques[2].fin == datetime(2024, 4, 2, 17, 0, tzinfo=TZ_CHILE)
        assert bloques[3].inicio == datetime(2024, 4, 3, 14, 0, tzinfo=TZ_CHILE)
