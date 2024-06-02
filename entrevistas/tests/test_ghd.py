from datetime import datetime

import pytest
from django.contrib.auth.models import User

from entrevistas.ghd import Horario, HorarioGlobal
from entrevistas.models import Sicologo
from utils.fechas import TZ_CHILE


@pytest.mark.django_db
class TestGeneradorDeHorasDeDisponibilidad:
    def _create_entrevistador(self):
        user = User.objects.create_user(username="entrevistador")
        return Sicologo.objects.create(usuario=user)

    def _create_entrevistador1(self):
        user = User.objects.create_user(username="entrevistador1")
        return Sicologo.objects.create(usuario=user)

    def _create_entrevistador2(self):
        user = User.objects.create_user(username="entrevistador2")
        return Sicologo.objects.create(usuario=user)

    def test_gdh_sin_bloqueos(self):
        entrevistador = self._create_entrevistador()
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
        entrevistador = self._create_entrevistador()
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
        entrevistador = self._create_entrevistador()
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
        entrevistador = self._create_entrevistador()
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

    def test_gdh_sobrelape(self):
        entrevistador = self._create_entrevistador()
        horario = Horario(entrevistador)
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=11,
            minuto_fin=0,
        )
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=11,
            minuto_inicio=0,
            hora_fin=14,
            minuto_fin=0,
        )
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=13,
            minuto_inicio=59,
            hora_fin=18,
            minuto_fin=0,
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(bloques) == 1
        assert bloques[0].inicio == datetime(2024, 4, 1, 8, 0, tzinfo=TZ_CHILE)
        assert bloques[0].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

    def test_gdh_precision(self):
        entrevistador = self._create_entrevistador()
        horario = Horario(entrevistador)
        entrevistador.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=11,
            minuto_fin=0,
        )

        bloques = horario.generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 4, 1, 8, 30, tzinfo=TZ_CHILE),  # lunes
            fecha_fin=datetime(2024, 4, 1, 10, 55, tzinfo=TZ_CHILE),  # lunes
        )

        assert len(bloques) == 1
        assert bloques[0].inicio == datetime(2024, 4, 1, 8, 30, tzinfo=TZ_CHILE)
        assert bloques[0].fin == datetime(2024, 4, 1, 10, 55, tzinfo=TZ_CHILE)

    def test_horario_global_sin_sobrelape(self):
        user1 = self._create_entrevistador1()
        user2 = self._create_entrevistador2()

        user1.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        user2.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=14,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )

        horario_global = HorarioGlobal().generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(horario_global) == 2
        assert horario_global[0].inicio == datetime(2024, 4, 1, 8, 0, tzinfo=TZ_CHILE)
        assert horario_global[0].fin == datetime(2024, 4, 1, 12, 0, tzinfo=TZ_CHILE)
        assert horario_global[1].inicio == datetime(2024, 4, 1, 14, 0, tzinfo=TZ_CHILE)
        assert horario_global[1].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

    def test_horario_global_con_sobrelape(self):
        user1 = self._create_entrevistador1()
        user2 = self._create_entrevistador2()

        user1.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        user2.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=10,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )

        horario_global = HorarioGlobal().generar_bloques_disponibles(
            fecha_inicio=datetime(2024, 3, 30, 0, 0, tzinfo=TZ_CHILE),  # sábado
            fecha_fin=datetime(2024, 4, 3, 23, 59, tzinfo=TZ_CHILE),  # miércoles
        )

        assert len(horario_global) == 1
        assert horario_global[0].inicio == datetime(2024, 4, 1, 8, 0, tzinfo=TZ_CHILE)
        assert horario_global[0].fin == datetime(2024, 4, 1, 18, 0, tzinfo=TZ_CHILE)

    def test_obtener_entrevistadores(self):
        user1 = self._create_entrevistador1()
        user2 = self._create_entrevistador2()
        user3 = self._create_entrevistador()

        user1.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=8,
            minuto_inicio=0,
            hora_fin=12,
            minuto_fin=0,
        )
        user2.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=10,
            minuto_inicio=0,
            hora_fin=18,
            minuto_fin=0,
        )
        user3.horarios_disponibles.create(
            dia="lunes",
            hora_inicio=11,
            minuto_inicio=30,
            hora_fin=12,
            minuto_fin=30,
        )

        fn = HorarioGlobal().obtener_entrevistadores

        assert fn("2024-03-31 11:30", "2024-03-31 12:00") == []
        assert fn("2024-04-01 7:30", "2024-04-01 8:00") == []
        assert fn("2024-04-01 8:00", "2024-04-01 8:30") == [user1]
        assert fn("2024-04-01 10:00", "2024-04-01 10:30") == [user1, user2]
        assert fn("2024-04-01 11:30", "2024-04-01 12:00") == [user1, user2, user3]
        assert fn("2024-04-01 12:00", "2024-04-01 12:30") == [user2, user3]
        assert fn("2024-04-01 12:30", "2024-04-01 13:00") == [user2]
        assert fn("2024-04-01 18:00", "2024-04-01 18:30") == []
        assert fn("2024-04-02 11:30", "2024-04-02 12:00") == []
