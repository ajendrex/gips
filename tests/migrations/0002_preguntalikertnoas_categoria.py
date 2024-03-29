# Generated by Django 5.0.2 on 2024-03-23 03:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="preguntalikertnoas",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("COGNITIVA", "Cognitiva"),
                    ("MOTORA", "Motora"),
                    ("NO_PLANIFICADA", "No planificada"),
                ],
                default="MOTORA",
                max_length=20,
            ),
            preserve_default=False,
        ),
    ]
