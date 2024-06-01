# Generated by Django 5.0.2 on 2024-06-01 03:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("entrevistas", "0009_rename_entrevistador_sicologo"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sicologo",
            options={"verbose_name": "Sicólogo"},
        ),
        migrations.AddField(
            model_name="sicologo",
            name="firma",
            field=models.ImageField(default="/an/invalid/path", upload_to="firmas/"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sicologo",
            name="nro_registro",
            field=models.CharField(default="9999", max_length=20),
            preserve_default=False,
        ),
    ]
