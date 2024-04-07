from datetime import datetime, timedelta
from typing import Union

from django.utils.timezone import localtime

from entrevistas.models import TZ_CHILE, Entrevistador

weekday_to_str = {
    0: "lunes",
    1: "martes",
    2: "miercoles",
    3: "jueves",
    4: "viernes",
    5: "sabado",
    6: "domingo",
}

MINUTOS_BLOQUE_ENTREVISTA = 30


class BloqueHorario:
    def __init__(self, hora_inicio: datetime, hora_fin: datetime):
        self.inicio = hora_inicio
        self.fin = hora_fin

    def __str__(self):
        return f'{self.inicio} - {self.fin}'

    def fecha(self):
        return self.inicio.date()

    def to_dict(self) -> dict[str, datetime]:
        return {
            "inicio": self.inicio,
            "fin": self.fin,
        }


class Horario:
    def __init__(self, entrevistador: Entrevistador):
        self.entrevistador = entrevistador

    def generar_bloques_disponibles(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[BloqueHorario]:
        fecha_inicio = localtime(fecha_inicio)
        fecha_fin = localtime(fecha_fin)
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

                    if disp.fin > bloqueo.fin:  # we should insert a new block
                        disponibilidad.insert(i_disp + 1, BloqueHorario(bloqueo.fin, disp.fin))

                    disp.fin = bloqueo.inicio

                else:  # we know disp.inicio < bloqueo.fin from (A) and bloqueo.fin < disp.fin from (C)
                    disp.inicio = bloqueo.fin

        return disponibilidad

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
                inicio = datetime(fecha.year, fecha.month, fecha.day, disp.hora_inicio, disp.minuto_inicio, tzinfo=TZ_CHILE)

                if inicio >= fecha_fin:  # no more blocks to add
                    break

                if inicio < fecha_inicio:
                    inicio = fecha_inicio

                fin = datetime(fecha.year, fecha.month, fecha.day, disp.hora_fin, disp.minuto_fin, tzinfo=TZ_CHILE)

                if fin > fecha_fin:
                    fin = fecha_fin

                try:
                    if disponibilidad[-1].fin >= inicio:
                        disponibilidad[-1].fin = fin
                        continue
                except IndexError:
                    pass

                if (fin - inicio) >= timedelta(minutes=MINUTOS_BLOQUE_ENTREVISTA):
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

        bloqueos_manuales = [
            BloqueHorario(localtime(bloqueo.fecha_inicio), localtime(bloqueo.fecha_fin))
            for bloqueo in bloqueos
        ]

        entrevistas = self.entrevistador.entrevistas.filter(
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio,
        ).order_by(
            "fecha_inicio",
        )

        bloqueos_entrevistas = [
            BloqueHorario(entrevista.fecha_inicio, entrevista.fecha_fin)
            for entrevista in entrevistas
        ]

        return sorted(bloqueos_manuales + bloqueos_entrevistas, key=lambda bloqueo: bloqueo.inicio)


class HorarioGlobal:
    def __init__(self):
        self.entrevistadores = Entrevistador.objects.filter(horarios_disponibles__isnull=False)

    def generar_bloques_disponibles(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[BloqueHorario]:
        horarios = self._generar_horarios(fecha_inicio, fecha_fin).values()

        minutos = set()

        for horario in horarios:
            for bloque in horario:
                minuto = bloque.inicio

                while minuto <= bloque.fin:
                    minutos.add(minuto)
                    minuto += timedelta(minutes=1)

        horario_global = []
        minutos = list(sorted(minutos))
        bloque = None

        for min in minutos:
            if bloque is None:
                bloque = BloqueHorario(min, min)
            elif min - bloque.fin == timedelta(minutes=1):
                bloque.fin = min
            else:
                if bloque.fin - bloque.inicio >= timedelta(minutes=15):
                    horario_global.append(bloque)
                bloque = BloqueHorario(min, min)

        if bloque.fin - bloque.inicio >= timedelta(minutes=15):
            horario_global.append(bloque)

        return horario_global

    def obtener_entrevistadores(self, inicio: Union[datetime, str], fin: Union[datetime, str]) -> list[Entrevistador]:
        if isinstance(inicio, str):
            inicio = datetime.strptime(inicio, "%Y-%m-%d %H:%M").astimezone(TZ_CHILE)

        if isinstance(fin, str):
            fin = datetime.strptime(fin, "%Y-%m-%d %H:%M").astimezone(TZ_CHILE)

        horarios_dict = self._generar_horarios(inicio, fin)

        return [
            entrevistador
            for entrevistador, horarios in horarios_dict.items()
            if len(horarios) == 1 and horarios[0].inicio == inicio and horarios[0].fin == fin
        ]

    def _generar_horarios(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[Entrevistador, list[BloqueHorario]]:
        return {
            entrevistador: Horario(entrevistador).generar_bloques_disponibles(fecha_inicio, fecha_fin)
            for entrevistador in self.entrevistadores
        }
