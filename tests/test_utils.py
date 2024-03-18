import datetime

import pytest

from ask_ai.conversation import utils


@pytest.mark.django_db
def test_format_chat_name(mrs_tiggywinkle_chat):
    chats = mrs_tiggywinkle_chat
    formatted_name = utils.format_chat_name(chats[0])
    assert len(formatted_name) == 43, formatted_name  # 40 chars + 3 dots
    assert "truncated" not in formatted_name, formatted_name
    formatted_name = utils.format_chat_name(chats[1])
    expected = chats[1].created_at.strftime(utils.UNNAMED_CHAT_DATE_FORMAT)
    assert formatted_name == expected, formatted_name


@pytest.mark.parametrize(
    "start_date,end_date,expected",
    [
        (None, None, 2),
        (datetime.datetime(2020, 12, 1), datetime.datetime(2022, 10, 2), 2),
        (datetime.datetime(2020, 12, 1), None, 2),
        (None, datetime.datetime(2022, 10, 3), 2),
        (datetime.datetime(2021, 1, 1), None, 1),
        (None, datetime.datetime(2021, 1, 1), 1),
    ],
)
@pytest.mark.django_db
def test_get_chats_for_user_created_between(multiple_chats_for_user, start_date, end_date, expected):
    user = multiple_chats_for_user
    chats = utils.get_chats_for_user_created_between(user, start_date, end_date)
    assert len(chats) == expected, chats


@pytest.mark.django_db
def test_get_all_valid_prompts_from_chat(peter_chat):
    all_valid_prompts = utils.get_all_valid_prompts_from_chat(peter_chat)
    assert all_valid_prompts.count() == 2, all_valid_prompts.count()
    user_prompt_values = all_valid_prompts.values_list("user_prompt", flat=True)
    assert "Flagged sensitive prompt, shouldn't be blocked" in user_prompt_values, user_prompt_values
    assert "What is the capital of Spain?" in user_prompt_values, user_prompt_values
