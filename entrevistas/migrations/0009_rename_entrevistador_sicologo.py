# Generated by Django 5.0.2 on 2024-06-01 03:38

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("entrevistas", "0008_alter_entrevista_resultado"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Entrevistador",
            new_name="Sicologo",
        ),
    ]