# Generated by Django 4.2.6 on 2023-10-12 18:35

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("conversation", "0009_rename_flagged_sensitive_prompt_potentially_sensitive_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="prompt",
            name="raw_ai_response",
        ),
        migrations.RemoveField(
            model_name="prompt",
            name="raw_user_prompt",
        ),
    ]
