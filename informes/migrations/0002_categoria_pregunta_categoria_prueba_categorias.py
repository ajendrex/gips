# Generated by Django 5.0.2 on 2024-03-07 00:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("informes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Categoria",
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
                ("nombre", models.CharField(max_length=255, unique=True)),
                ("descripcion", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Categoría",
                "verbose_name_plural": "Categorías",
            },
        ),
        migrations.AddField(
            model_name="pregunta",
            name="categoria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="informes.categoria",
            ),
        ),
        migrations.AddField(
            model_name="prueba",
            name="categorias",
            field=models.ManyToManyField(blank=True, to="informes.categoria"),
        ),
    ]