# Generated by Django 3.2 on 2021-04-27 19:05

from django.db import migrations, models
import shareit.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Resource",
            fields=[
                (
                    "uid",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("url", models.CharField(max_length=50)),
                ("secret_hash", models.CharField(max_length=64)),
                ("expiration_date", models.DateTimeField(default=shareit.models.expiration_date)),
                ("accessed", models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
