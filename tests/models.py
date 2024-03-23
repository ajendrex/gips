import reversion
from django.db import models
from django_countries.fields import CountryField


@reversion.register()
class Persona(models.Model):
    rut = models.CharField(max_length=12)
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    nacionalidad = CountryField()
    fecha_nacimiento = models.DateField("fecha de nacimiento")
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True)

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}".strip()


class Test(models.Model):
    nombre = models.CharField(max_length=100)
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
    score_nunca = models.IntegerField("Nunca o casi nunca", default=1)
    score_ocasionalmente = models.IntegerField("Ocasionalmente", default=2)
    score_a_menudo = models.IntegerField("A menudo", default=3)
    score_siempre = models.IntegerField("Siempre o casi siempre", default=4)


class Resultado(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name="resultados")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="resultados")
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

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
