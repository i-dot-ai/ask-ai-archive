import datetime
from typing import Optional

from . import models

UNNAMED_CHAT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def format_chat_name(chat):
    length_to_truncate = 40
    chat_created_str = chat.created_at.strftime(UNNAMED_CHAT_DATE_FORMAT)
    first_prompt = chat.prompt_set.order_by("created_at").first()
    if not first_prompt:
        return chat_created_str
    name = first_prompt.user_prompt
    if not name:
        name = chat_created_str
    elif len(name) > length_to_truncate:
        name = f"{name[:length_to_truncate]}..."
    return name


def get_chats_for_user_created_between(
    user: type[models.User], start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None
) -> list:
    # start and end inclusive
    chats_for_user = models.Chat.objects.filter(user=user).prefetch_related("prompt_set")
    if start_date:
        chats_for_user = chats_for_user.filter(modified_at__date__gte=start_date)
    if end_date:
        chats_for_user = chats_for_user.filter(modified_at__date__lte=end_date)
    chats_for_user.order_by("-created_at")
    chats = [{"name": format_chat_name(chat), "id": chat.id} for chat in chats_for_user]
    return chats


def get_all_valid_prompts_from_chat(chat):
    all_prompts_for_chat = models.Prompt.objects.filter(chat=chat)
    all_valid_chat_prompts = (
        # Assume chat is sensitive if flagged as sensitive
        # unless explicitly marked not sensitive by user
        # First condition corresponds to `is_sensitve` (can't use properties in querysets)
        all_prompts_for_chat.exclude(potentially_sensitive=True, user_confirmed_not_sensitive=False)
        .exclude(user_prompt_moderated=True)
        .exclude(ai_response_moderated=True)
        .exclude(api_call_error=True)
        .order_by("created_at")
    )
    return all_valid_chat_prompts


def get_form_errors_as_strings(form_errors):
    errors = form_errors.as_data()
    errors_output = dict()
    for k, v in errors.items():
        error_msgs = [e.messages for e in v]
        error_list = [" ".join(e) for e in error_msgs]
        error_str = " ".join(error_list)
        errors_output[k] = error_str
    return errors_output
