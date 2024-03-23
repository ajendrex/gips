import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django_countries.fields import CountryField
from chile_rut import validate_rut

from utils.text import alfanumerico_random


class RUTField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verbose_name", "RUT")
        kwargs["max_length"] = 12
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if not validate_rut(value):
            raise ValidationError("RUT inválido")


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


class PreguntaBase(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    texto = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.texto


class PreguntaLikertNOAS(PreguntaBase):
    categoria = models.CharField(
        max_length=20,
        choices=(
            ("COGNITIVA", "Cognitiva"),
            ("MOTORA", "Motora"),
            ("NO_PLANIFICADA", "No planificada"),
        )
    )
    score_nunca = models.IntegerField("Nunca o casi nunca", default=1)
    score_ocasionalmente = models.IntegerField("Ocasionalmente", default=2)
    score_a_menudo = models.IntegerField("A menudo", default=3)
    score_siempre = models.IntegerField("Siempre o casi siempre", default=4)


class AccesoTest(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="accesos")
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_vencimiento = models.DateTimeField("fecha de vencimiento")
    mandante = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="accesos_mandante")

    def __str__(self):
        return f"{self.persona} - {self.test} - {self.fecha_creacion}"


class AccesoTestPersona(models.Model):
    acceso_test = models.ForeignKey(AccesoTest, on_delete=models.CASCADE, related_name="ruts")
    persona = models.ForeignKey(Persona, on_delete=models.RESTRICT, related_name="accesos")
    codigo = models.CharField(max_length=20, unique=True)

    class Meta:
        unique_together = ("acceso_test", "persona")

    def save(self, *args, **kwargs):
        self.codigo = alfanumerico_random(20)
        super().save(*args, **kwargs)


class Resultado(models.Model):
    acceso = models.ForeignKey(AccesoTest, on_delete=models.CASCADE, related_name="resultados")
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="resultados")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="resultados")
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        unique_together = ("persona", "test")

    def __str__(self):
        return f"{self.persona} - {self.test} - {self.fecha_creacion}"


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
    score = models.IntegerField()

    class Meta:
        unique_together = ("resultado", "pregunta")

    def __str__(self):
        return f"{self.resultado} - {self.pregunta} - {self.alternativa}"
