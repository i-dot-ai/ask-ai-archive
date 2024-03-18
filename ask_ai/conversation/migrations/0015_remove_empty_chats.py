# Delete empty chats ie no related prompts

from django.db import migrations


def delete_empty_models(apps, schema_editor):
    Chat = apps.get_model("conversation", "Chat")
    empty_chats = Chat.objects.filter(prompt__isnull=True)
    empty_chats.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conversation", "0014_remove_chat_chat_ended"),
    ]

    operations = [migrations.RunPython(delete_empty_models)]
