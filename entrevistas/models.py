from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.db import models

from tests.models import Persona, AccesoTestPersona, Resultado, ResultadoEvaluacion, Test


class Sicologo(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.RESTRICT, related_name="entrevistador")
    nro_registro = models.CharField(max_length=20, blank=False)
    firma = models.ImageField(upload_to="firmas/", blank=False)
    genero = models.CharField(max_length=1, choices=(("M", "Masculino"), ("F", "Femenino")))
    titulo = models.CharField("título", max_length=100, blank=False, help_text="Ej: Psicólogo Clínico")

    class Meta:
        verbose_name = "Sicólogo"

    def __str__(self):
        return self.usuario.get_full_name()

    @property
    def first_name(self):
        return self.usuario.first_name

    @property
    def last_name(self):
        return self.usuario.last_name


class Entrevista(models.Model):
    entrevistador = models.ForeignKey(Sicologo, on_delete=models.RESTRICT, related_name="entrevistas")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    acceso = models.ForeignKey(AccesoTestPersona, on_delete=models.RESTRICT, related_name="entrevistas")
    resultado = models.OneToOneField(Resultado, on_delete=models.RESTRICT, related_name="entrevista", null=True)
    observaciones = models.TextField(blank=True)
    resultado_entrevista = models.ForeignKey(
        ResultadoEvaluacion,
        on_delete=models.RESTRICT,
        related_name="entrevistas",
        null=True,
        blank=True,
        help_text="Si se indica un valor, este tiene precedencia sobre el resultado del test."
    )

    def __str__(self):
        return f"{self.entrevistador} : {self.entrevistado} el {self.fecha}"

    @property
    def entrevistado(self) -> Persona:
        return self.acceso.persona

    @property
    def fecha(self) -> datetime:
        return self.fecha_inicio

    @property
    def test(self) -> Test:
        return self.acceso.test


HORA_CHOICES = (
    (0, "0 AM"),
    (1, "1 AM"),
    (2, "2 AM"),
    (3, "3 AM"),
    (4, "4 AM"),
    (5, "5 AM"),
    (6, "6 AM"),
    (7, "7 AM"),
    (8, "8 AM"),
    (9, "9 AM"),
    (10, "10 AM"),
    (11, "11 AM"),
    (12, "12 PM"),
    (13, "1 PM"),
    (14, "2 PM"),
    (15, "3 PM"),
    (16, "4 PM"),
    (17, "5 PM"),
    (18, "6 PM"),
    (19, "7 PM"),
    (20, "8 PM"),
    (21, "9 PM"),
    (22, "10 PM"),
    (23, "11 PM"),
)

MINUTO_CHOICES = (
    (0, "00"),
    (15, "15"),
    (30, "30"),
    (45, "45"),
)


class Disponibilidad(models.Model):
    entrevistador = models.ForeignKey(Sicologo, on_delete=models.CASCADE, related_name="horarios_disponibles")
    dia = models.CharField(
        "día",
        max_length=9,
        choices=(
            ("lunes", "Lunes"),
            ("martes", "Martes"),
            ("miercoles", "Miércoles"),
            ("jueves", "Jueves"),
            ("viernes", "Viernes"),
            ("sabado", "Sábado"),
            ("domingo", "Domingo"),
        ),
    )
    hora_inicio = models.IntegerField(choices=HORA_CHOICES)
    minuto_inicio = models.IntegerField(choices=MINUTO_CHOICES)
    hora_fin = models.IntegerField(choices=HORA_CHOICES)
    minuto_fin = models.IntegerField(choices=MINUTO_CHOICES)

    class Meta:
        verbose_name_plural = "disponibilidades"


class Bloqueo(models.Model):
    entrevistador = models.ForeignKey(Sicologo, on_delete=models.CASCADE, related_name="bloqueos")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.TextField()
