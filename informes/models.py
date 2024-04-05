import reversion
from django.contrib.auth.models import User
from django.db import models


@reversion.register()
class Persona(models.Model):
    rut = models.CharField(max_length=255, unique=True)  # Format must be 12.345.678-9
    nombres = models.CharField(max_length=255)
    apellido_paterno = models.CharField(max_length=255)
    apellido_materno = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    nacionalidad = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}".strip()


class AlgoritmoEvaluacion(models.Model):
    nombre = models.CharField(max_length=255)
    clase = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Algoritmo de evaluación'
        verbose_name_plural = 'Algoritmos de evaluación'

    def __str__(self):
        return f"{self.nombre} ({self.clase})"


class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Prueba(models.Model):
    nombre = models.CharField(max_length=255)
    plataforma = models.CharField(max_length=255)
    id_plataforma = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    algoritmo_evaluacion = models.ForeignKey(AlgoritmoEvaluacion, on_delete=models.RESTRICT, null=True, blank=True)
    parametros = models.JSONField(null=True)
    metadata = models.JSONField()
    categorias = models.ManyToManyField(Categoria, blank=True)

    class Meta:
        unique_together = ('plataforma', 'id_plataforma')

    def __str__(self):
        return f"{self.nombre} ({self.plataforma})"


class Pregunta(models.Model):
    prueba = models.ForeignKey(Prueba, on_delete=models.RESTRICT, related_name='preguntas')
    pagina = models.IntegerField()
    posicion = models.IntegerField()
    tipo = models.CharField(max_length=255)
    plataforma = models.CharField(max_length=255)
    id_plataforma = models.CharField(max_length=255)
    texto = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        unique_together = ('prueba_id', 'plataforma', 'id_plataforma')

    def __str__(self):
        return self.texto


class Alternativa(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='alternativas')
    posicion = models.IntegerField()
    id_plataforma = models.CharField(max_length=255)
    texto = models.TextField()
    puntaje = models.FloatField()

    def __str__(self):
        return f"{self.texto} ({self.puntaje})"


class Resultado(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.RESTRICT, null=True, blank=True)
    prueba = models.ForeignKey(Prueba, on_delete=models.RESTRICT, related_name='resultados')
    id_plataforma = models.CharField(max_length=255)
    fecha = models.DateTimeField()
    metadata = models.JSONField()
    evaluacion = models.JSONField(null=True)
    informe = models.FileField(upload_to='informes/%Y/%m/%d/', null=True)
    clave_archivo = models.CharField(max_length=20, null=True, blank=True)
    clave_acceso = models.CharField(max_length=255, unique=True, null=True)
    email_envio = models.EmailField(null=True, blank=True)

    class Meta:
        unique_together = ('prueba', 'id_plataforma')

    def __str__(self):
        return f"{self.persona} - {self.prueba}"


class Respuesta(models.Model):
    resultado = models.ForeignKey(Resultado, on_delete=models.RESTRICT, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.RESTRICT, related_name='respuestas')
    valor = models.CharField(max_length=255, blank=True)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.RESTRICT, null=True, blank=True)
    metadata = models.JSONField()

    class Meta:
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        return f"{self.resultado} - {self.pregunta}"


class EnvioEmail(models.Model):
    resultado = models.ForeignKey(Resultado, on_delete=models.RESTRICT)
    fecha = models.DateTimeField()
    destinatario = models.EmailField()
    mensaje = models.TextField()

    class Meta:
        verbose_name = 'Envío de email'
        verbose_name_plural = 'Envíos de email'

    def __str__(self):
        return f"{self.resultado} - {self.destinatario} ({self.fecha})"


class Entrevista(models.Model):
    resultado = models.OneToOneField(Resultado, on_delete=models.RESTRICT, related_name='entrevista')
    fecha = models.DateTimeField()
    observaciones = models.TextField()
    plataforma = models.CharField(
        max_length=255,
        choices=(
            ('whatsapp', 'WhatsApp'),
            ('zoom', 'Zoom'),
            ('meet', 'Google Meet'),
        )
    )

    def __str__(self):
        return f"{self.resultado} - ({self.fecha})"


class Sicologo(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.RESTRICT, related_name='sicologo')
    usuario = models.OneToOneField(User, on_delete=models.RESTRICT, related_name='sicologo')

    def __str__(self):
        return f"{self.persona} ({self.usuario})"
