from django.db import models


class Persona(models.Model):
    rut = models.CharField(max_length=255, unique=True)
    nombres = models.CharField(max_length=255)
    apellido_paterno = models.CharField(max_length=255)
    apellido_materno = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"


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
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    algoritmo_evaluacion = models.ForeignKey(AlgoritmoEvaluacion, on_delete=models.RESTRICT, null=True)
    parametros_evaluacion = models.JSONField(null=True)
    metadata = models.JSONField()
    categorias = models.ManyToManyField(Categoria, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.plataforma})"


class Pregunta(models.Model):
    prueba = models.ForeignKey(Prueba, on_delete=models.CASCADE, related_name='preguntas')
    pagina = models.IntegerField()
    posicion = models.IntegerField()
    id_externo = models.CharField(max_length=255)
    texto = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, null=True, blank=True)

    def __str__(self):
        return f"({self.pagina}.{self.posicion})"


class Alternativa(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='alternativas')
    posicion = models.IntegerField()
    id_externo = models.CharField(max_length=255)
    texto = models.TextField()
    puntaje = models.FloatField()

    def __str__(self):
        return f"{self.texto} ({self.puntaje})"


class Resultado(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.RESTRICT)
    prueba = models.ForeignKey(Prueba, on_delete=models.RESTRICT, related_name='resultados')
    fecha = models.DateTimeField()
    metadata = models.JSONField()
    informe = models.FileField(upload_to='informes/', null=True)
    clave_acceso = models.CharField(max_length=255, unique=True)
    email_envio = models.EmailField(null=True)

    def __str__(self):
        return f"{self.persona} - {self.prueba} ({self.fecha})"


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
    resultado = models.ForeignKey(Resultado, on_delete=models.RESTRICT)
    fecha = models.DateTimeField()
    entrevistador = models.ForeignKey(Persona, on_delete=models.RESTRICT)
    observaciones = models.TextField()
    plataforma = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.resultado} - {self.entrevistador} ({self.fecha})"
