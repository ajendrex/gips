# Generated by Django 5.0.2 on 2024-03-06 02:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AlgoritmoEvaluacion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=255)),
                ("clase", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Algoritmo de evaluación",
                "verbose_name_plural": "Algoritmos de evaluación",
            },
        ),
        migrations.CreateModel(
            name="Persona",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rut", models.CharField(max_length=255, unique=True)),
                ("nombres", models.CharField(max_length=255)),
                ("apellido_paterno", models.CharField(max_length=255)),
                ("apellido_materno", models.CharField(max_length=255)),
                ("fecha_nacimiento", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="Pregunta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("pagina", models.IntegerField()),
                ("posicion", models.IntegerField()),
                ("id_externo", models.CharField(max_length=255)),
                ("texto", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="Alternativa",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("posicion", models.IntegerField()),
                ("id_externo", models.CharField(max_length=255)),
                ("texto", models.TextField()),
                ("puntaje", models.FloatField()),
                (
                    "pregunta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alternativas",
                        to="informes.pregunta",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Prueba",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=255)),
                ("plataforma", models.CharField(max_length=255)),
                ("fecha_creacion", models.DateTimeField()),
                ("fecha_actualizacion", models.DateTimeField()),
                ("parametros_evaluacion", models.JSONField(null=True)),
                ("metadata", models.JSONField()),
                (
                    "algoritmo_evaluacion",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="informes.algoritmoevaluacion",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="pregunta",
            name="prueba",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="preguntas",
                to="informes.prueba",
            ),
        ),
        migrations.CreateModel(
            name="Resultado",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateTimeField()),
                ("metadata", models.JSONField()),
                ("informe", models.FileField(null=True, upload_to="informes/")),
                ("clave_acceso", models.CharField(max_length=255, unique=True)),
                ("email_envio", models.EmailField(max_length=254, null=True)),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="informes.persona",
                    ),
                ),
                (
                    "prueba",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="resultados",
                        to="informes.prueba",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EnvioEmail",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateTimeField()),
                ("destinatario", models.EmailField(max_length=254)),
                ("mensaje", models.TextField()),
                (
                    "resultado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="informes.resultado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Envío de email",
                "verbose_name_plural": "Envíos de email",
            },
        ),
        migrations.CreateModel(
            name="Entrevista",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateTimeField()),
                ("observaciones", models.TextField()),
                ("plataforma", models.CharField(max_length=255)),
                (
                    "entrevistador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="informes.persona",
                    ),
                ),
                (
                    "resultado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="informes.resultado",
                    ),
                ),
            ],
        ),
    ]
