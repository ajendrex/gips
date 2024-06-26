# Generated by Django 5.0.2 on 2024-05-12 03:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0009_gentilicio"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gentilicio",
            name="gentilicio",
            field=models.CharField(
                help_text='Gentilicio en género femenino, para ser usado después de "de nacionalidad". Ejemplo: "chilena"',
                max_length=100,
            ),
        ),
    ]
