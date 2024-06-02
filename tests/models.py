from datetime import datetime
from typing import Dict, Set

import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import make_aware
from django_countries.fields import CountryField
from rut_chile import rut_chile

from utils.fechas import TZ_CHILE
from utils.text import alfanumerico_random


class RUTField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verbose_name", "RUT")
        kwargs["max_length"] = 12
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if not rut_chile.is_valid_rut(value):
            raise ValidationError("RUT inválido")


class Gentilicio(models.Model):
    pais = CountryField(unique=True)
    gentilicio = models.CharField(
        max_length=100,
        help_text='Gentilicio en género femenino, para ser usado después de "de nacionalidad". Ejemplo: "chilena"',
    )

    def __str__(self):
        return f"{self.gentilicio} ({self.pais})"


@reversion.register()
class Persona(models.Model):
    rut = RUTField(unique=True)
    nombres = models.CharField("nombres o razón social", max_length=100)
    es_natural = models.BooleanField("es persona natural", default=True)
    apellido_paterno = models.CharField(max_length=100, blank=True)
    apellido_materno = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    nacionalidad = CountryField(blank=True)
    fecha_nacimiento = models.DateField("fecha de nacimiento", null=True, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True)

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}".strip()


class Contacto(models.Model):
    persona_juridica = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="contactos")
    persona_natural = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="empresas")


class Test(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True)

    def __str__(self):
        return self.nombre

    @property
    def categorias_tramos(self) -> Set[str]:
        return set(self.tramos.values_list("categoria", flat=True).distinct())


class TramoCategoriaEvaluacion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="tramos")
    categoria = models.CharField(
        "categoría",
        max_length=100,
        choices=(
            ("GENERAL", "General"),
            ("COGNITIVA", "Cognitiva"),
            ("MOTORA", "Motora"),
            ("NO_PLANIFICADA", "No planificada"),
        ),
    )
    nombre = models.CharField(max_length=100, choices=(("BAJO", "Bajo"), ("MODERADO", "Moderado"), ("ALTO", "Alto")))
    texto = models.TextField("texto")
    puntaje_minimo = models.IntegerField("puntaje mínimo")
    puntaje_maximo = models.IntegerField("puntaje máximo")

    class Meta:
        unique_together = ("test", "categoria", "nombre")
        verbose_name = "Tramo de categoría de evaluación"
        verbose_name_plural = "Tramos de categorías de evaluación"

    def __str__(self):
        return f"{self.categoria} - {self.nombre}"


class ResultadoEvaluacion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="resultados_posibles")
    nombre = models.CharField(max_length=100)
    texto = models.TextField()

    class Meta:
        unique_together = ("test", "nombre")
        verbose_name = "Resultado de evaluación"
        verbose_name_plural = "Resultados de evaluación"

    def __str__(self):
        return self.nombre


class PreguntaBase(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    texto = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.texto


class PreguntaLikertNOAS(PreguntaBase):
    categoria = models.CharField(
        "categoría",
        max_length=20,
        choices=(
            ("COGNITIVA", "Cognitiva"),
            ("MOTORA", "Motora"),
            ("NO_PLANIFICADA", "No planificada"),
        )
    )
    puntaje_nunca = models.IntegerField("Nunca o casi nunca", default=1)
    puntaje_ocasionalmente = models.IntegerField("Ocasionalmente", default=2)
    puntaje_a_menudo = models.IntegerField("A menudo", default=3)
    puntaje_siempre = models.IntegerField("Siempre o casi siempre", default=4)


class Cargo(models.TextChoices):
    NOCHERO = "NOCHERO", "Nochero"
    RONDIN = "RONDIN", "Rondín"
    PORTERO = "PORTERO", "Portero"
    CONSERJE = "CONSERJE", "Conserje"
    VIGILANTE_PRIVADO = "VIGILANTE_PRIVADO", "Vigilante Privado"
    GUARDIA_DE_SEGURIDAD = "GUARDIA_DE_SEGURIDAD", "Guardia de Seguridad"
    ENCARGADO_DE_SEGURIDAD = "ENCARGADO_DE_SEGURIDAD", "Encargado de Seguridad"
    SUPERVISOR_DE_SEGURIDAD = "SUPERVISOR_DE_SEGURIDAD", "Supervisor de Seguridad"
    JEFE_DE_SEGURIDAD = "JEFE_DE_SEGURIDAD", "Jefe de Seguridad"
    ASESOR_DE_SEGURIDAD = "ASESOR_DE_SEGURIDAD", "Asesor de Seguridad"
    CAPACITADOR_DE_SEGURIDAD_PRIVADA = "CAPACITADOR_DE_SEGURIDAD_PRIVADA", "Capacitador de Seguridad Privada"
    INSTALADOR_TECNICO_DE_SEGURIDAD = "INSTALADOR_TECNICO_DE_SEGURIDAD", "Instalador Técnico de Seguridad"
    OPERADOR_DE_CCTV_Y_ALARMAS = "OPERADOR_DE_CCTV_Y_ALARMAS", "Operador de CCTV y Alarmas"


class AccesoTest(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="accesos")
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_vencimiento = models.DateTimeField("fecha de vencimiento")
    mandante = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="accesos_mandante")
    valor_unitario = models.IntegerField(default=12000)
    cargo_predefinido = models.CharField(max_length=50, choices=Cargo.choices, default=Cargo.GUARDIA_DE_SEGURIDAD)

    def __str__(self):
        return f"{self.test} - {self.mandante} - {self.fecha_creacion.date()} - {self.fecha_vencimiento.date()}"


class AccesoTestPersona(models.Model):
    acceso_test = models.ForeignKey(AccesoTest, on_delete=models.CASCADE, related_name="ruts")
    persona = models.ForeignKey(Persona, on_delete=models.RESTRICT, related_name="accesos")
    codigo = models.CharField(max_length=20, unique=True)
    inicio_respuestas_ts = models.DateTimeField("inicio test", null=True)
    fin_respuestas_ts = models.DateTimeField("término test", null=True)
    cargo = models.CharField(max_length=50, choices=Cargo.choices)

    class Meta:
        unique_together = ("acceso_test", "persona")

    def __str__(self):
        return f"{self.persona} - {self.acceso_test} - {self.codigo}"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo or alfanumerico_random(20)
        super().save(*args, **kwargs)

    def iniciar(self):
        self.inicio_respuestas_ts = make_aware(datetime.now(), timezone=TZ_CHILE)
        self.save()

    def finalizar(self):
        self.fin_respuestas_ts = make_aware(datetime.now(), timezone=TZ_CHILE)
        self.save()

    @property
    def tiempo_test(self) -> str:
        if not self.fin_respuestas_ts or not self.inicio_respuestas_ts:
            return "Sin Datos"

        total_segundos = (self.fin_respuestas_ts - self.inicio_respuestas_ts).seconds
        minutos = total_segundos // 60
        segundos = total_segundos % 60

        if minutos:
            tiempo_str = f"{minutos} minutos"
            if segundos:
                tiempo_str += f" y {segundos} segundos"
        else:
            tiempo_str = f"{segundos} segundos"

        return tiempo_str

    @property
    def test(self) -> Test:
        return self.acceso_test.test


class Resultado(models.Model):
    acceso = models.OneToOneField(AccesoTestPersona, on_delete=models.CASCADE, related_name="resultado")
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    clave_archivo = models.CharField(max_length=20, blank=True, default="")
    evaluacion = models.JSONField(default=dict)
    informe = models.FileField(upload_to='resultados/%Y/%m/%d/', null=True)

    def __str__(self):
        return f"{self.persona} - {self.test} - {self.fecha_creacion.date()}"

    @property
    def persona(self) -> Persona:
        return self.acceso.persona

    @property
    def test(self) -> Test:
        return self.acceso.acceso_test.test

    @property
    def codigo_acceso(self) -> str:
        return self.acceso.codigo


class RespuestaBase(models.Model):
    resultado = models.ForeignKey(Resultado, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.resultado} - {self.pregunta}"


class RespuestaLikertNOAS(RespuestaBase):
    pregunta = models.ForeignKey(PreguntaLikertNOAS, on_delete=models.CASCADE, related_name="respuestas")
    alternativa = models.CharField(
        max_length=1,
        choices=(
            ("N", "Nunca o casi nunca"),
            ("O", "Ocasionalmente"),
            ("A", "A menudo"),
            ("S", "Siempre o casi siempre"),
        ),
    )
    puntaje = models.IntegerField()

    class Meta:
        unique_together = ("resultado", "pregunta")

    def __str__(self):
        return f"{self.resultado} - {self.pregunta} - {self.alternativa}"

    def save(self, *args, **kwargs):
        self.puntaje = self.puntajes.get(self.alternativa)
        super().save(*args, **kwargs)

    @property
    def puntajes(self) -> Dict[str, int]:
        return {
            "N": self.pregunta.puntaje_nunca,
            "O": self.pregunta.puntaje_ocasionalmente,
            "A": self.pregunta.puntaje_a_menudo,
            "S": self.pregunta.puntaje_siempre,
        }

    @property
    def categoria(self) -> str:
        return self.pregunta.categoria
