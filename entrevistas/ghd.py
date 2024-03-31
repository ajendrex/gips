from datetime import datetime, timedelta

from django.contrib.auth.models import User


weekday_to_str = {
    0: "lunes",
    1: "martes",
    2: "miercoles",
    3: "jueves",
    4: "viernes",
    5: "sabado",
    6: "domingo",
}


class BloqueHorario:
    def __init__(self, hora_inicio: datetime, hora_fin: datetime):
        self.inicio = hora_inicio
        self.fin = hora_fin

    def __str__(self):
        return f'{self.inicio} - {self.fin}'

    def fecha(self):
        return self.inicio.date()

class Horario:
    def __init__(self, entrevistador: User):
        self.entrevistador = entrevistador

    def generar_bloques_disponibles(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[BloqueHorario]:
        disponibilidad = self._get_disponibilidad_base(fecha_inicio, fecha_fin)

        if not disponibilidad:
            return []

        bloqueos = self._get_bloqueos(fecha_inicio, fecha_fin)

        i_disp = 0

        for bloqueo in bloqueos:
            while i_disp < len(disponibilidad):
                disp = disponibilidad[i_disp]

                if disp.inicio >= bloqueo.fin:
                    break
                # disp.inicio < bloqueo.fin    (A)

                if disp.fin <= bloqueo.inicio:
                    i_disp += 1
                    continue
                # disp.fin > bloqueo.inicio     (B)

                if disp.inicio >= bloqueo.inicio and disp.fin <= bloqueo.fin:
                    disponibilidad.pop(i_disp)
                    continue
                # disp.inicio < bloqueo.inicio or disp.fin > bloqueo.fin     (C)

                if disp.inicio < bloqueo.inicio:  # and we know disp.fin > bloqueo.inicio from (B)
                    disp.fin = bloqueo.inicio

                    if disp.fin > bloqueo.fin:  # we should insert a new block
                        disponibilidad.insert(i_disp + 1, BloqueHorario(bloqueo.fin, disp.fin))

                else:  # we know disp.inicio < bloqueo.fin from (A) and bloqueo.fin < disp.fin from (C)
                    disp.inicio = bloqueo.fin

                i_disp += 1

    def _get_disponibilidad_base(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[BloqueHorario]:
        fecha = fecha_inicio.date()
        disponibilidad = []

        while fecha <= fecha_fin.date():
            horarios_disponibles = self.entrevistador.horarios_disponibles.filter(
                dia=weekday_to_str[fecha.weekday()]
            ).order_by(
                "hora_inicio", "minuto_inicio"
            )

            for disp in horarios_disponibles:
                inicio = datetime(fecha.year, fecha.month, fecha.day, disp.inicio, disp.minuto_inicio)

                if inicio > fecha_fin:  # no more blocks to add
                    break

                fin = datetime(fecha.year, fecha.month, fecha.day, disp.fin, disp.minuto_fin)

                if fin > fecha_fin:
                    fin = fecha_fin

                disponibilidad.append(BloqueHorario(inicio, fin))

                if fin == fecha_fin:  # no more blocks to add
                    break

            fecha += timedelta(days=1)

        return disponibilidad

    def _get_bloqueos(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[BloqueHorario]:
        bloqueos = self.entrevistador.bloqueos.filter(
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio,
        ).order_by(
            "fecha_inicio",
        )

        return [
            BloqueHorario(bloqueo.fecha_inicio, bloqueo.fecha_fin)
            for bloqueo in bloqueos
        ]
