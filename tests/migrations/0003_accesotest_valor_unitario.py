# Generated by Django 5.0.2 on 2024-03-24 01:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0002_preguntalikertnoas_categoria"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesotest",
            name="valor_unitario",
            field=models.IntegerField(default=12000),
        ),
    ]
