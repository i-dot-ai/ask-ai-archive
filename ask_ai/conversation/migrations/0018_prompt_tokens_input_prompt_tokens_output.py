# Generated by Django 4.2.8 on 2023-12-18 12:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("conversation", "0017_create_data_download_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="prompt",
            name="tokens_input",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="prompt",
            name="tokens_output",
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
