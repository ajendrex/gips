# Generated by Django 5.0.2 on 2024-06-15 15:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0017_remove_resultado_resultado_resultado_resultado_test"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultado",
            name="cerrado",
            field=models.BooleanField(default=False),
        ),
    ]
