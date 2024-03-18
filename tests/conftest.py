import base64
import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest
import pytz
from django.conf import settings
from django.contrib.auth.models import Group
from freezegun import freeze_time

from ask_ai.conversation import models
from ask_ai.conversation.login_views import ColaLoginForceDeclaration
from ask_ai.conversation.models import User

UTC = pytz.timezone("UTC")


@pytest.fixture
def create_user():
    def _create_user(email, date_joined_iso):
        date_joined = UTC.localize(datetime.fromisoformat(date_joined_iso))
        user = User.objects.create_user(email=email, date_joined=date_joined)
        return user

    return _create_user


@pytest.fixture
def alice(create_user):
    return create_user("alice@cabinetoffice.gov.uk", "2000-01-01")


@pytest.fixture
def bob(create_user):
    user = create_user("bob@example.com", "2000-01-01")

    group = Group.objects.get(name="Data download")
    user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def chris(create_user):
    return create_user("chris@example.com", "2000-01-02")


@pytest.fixture
def peter_rabbit(create_user):
    user = User.objects.create_user(email="peter.rabbit@example.com", password="P455W0rd")
    yield user


@pytest.fixture
def jemima_puddleduck():
    user = User.objects.create_user(email="jemima.puddleduck@example.com", password="P455W0rd")
    yield user


@pytest.fixture
def mrs_tiggywinkle():
    user = User.objects.create_user(email="mrs.tiggywinkle@example.com")
    yield user


@pytest.fixture
def peter_and_bob_chat(peter_rabbit, bob):
    chat_1 = models.Chat(user=peter_rabbit)
    chat_1.save()
    chat_2 = models.Chat(user=peter_rabbit)
    chat_2.save()
    chat_3 = models.Chat(user=bob)
    chat_3.save()
    models.Prompt(chat=chat_1, cost_input_dollars=0.3, cost_output_dollars=0.5).save()
    models.Prompt(chat=chat_1, cost_input_dollars=0.1, cost_output_dollars=0.2).save()
    models.Prompt(chat=chat_2, cost_input_dollars=0.15, cost_output_dollars=0.2, user_prompt="first prompt").save()
    models.Prompt(chat=chat_2, cost_input_dollars=0.5, cost_output_dollars=0.2).save()
    models.Prompt(chat=chat_3, cost_input_dollars=0.4, cost_output_dollars=0.4).save()


@pytest.fixture
def mrs_tiggywinkle_chat(mrs_tiggywinkle):
    chat1 = models.Chat(user=mrs_tiggywinkle)
    chat1.save()
    chat2 = models.Chat(user=mrs_tiggywinkle)
    chat2.save()
    long_user_prompt = "Here is a massive wall of text that goes on and on an on and on..... will this be truncated"
    super_long_prompt = models.Prompt(chat=chat1, user_prompt=long_user_prompt)
    super_long_prompt.save()
    yield chat1, chat2


@pytest.fixture
def peter_chat(peter_rabbit):
    with freeze_time("2024-01-01 12:00:01"):
        chat = models.Chat(user=peter_rabbit)
        chat.save()
        prompt = models.Prompt(chat=chat, user_prompt="What is the capital of Spain?", ai_response="Madrid")
        prompt.save()
        prompt = models.Prompt(chat=chat, user_prompt="Moderated prompt", user_prompt_moderated=True)
        prompt.save()
        prompt = models.Prompt(
            chat=chat,
            user_prompt="Flagged sensitive prompt, shouldn't be blocked",
            potentially_sensitive=True,
            user_confirmed_not_sensitive=True,
            ai_response="Some response",
        )
        prompt.save()
        prompt = models.Prompt(
            chat=chat,
            user_prompt="User confirmed sensitive prompt",
            potentially_sensitive=True,
            user_confirmed_not_sensitive=False,
        )
        prompt.save()
        prompt = models.Prompt(
            chat=chat, user_prompt="Response moderated", ai_response="Bad AI response", ai_response_moderated=True
        )
        prompt.save()
        prompt = models.Prompt(chat=chat, user_prompt="Error getting response from API", api_call_error=True)
        prompt.save()
    yield chat


@pytest.fixture
def peter_feedback(peter_rabbit):
    with freeze_time("2024-01-01 12:00:01"):
        feedback = models.Feedback(
            user=peter_rabbit,
            satisfaction="NO_OPINION",
            take_part_in_user_research=False,
            improve_the_service="Something that will improve the service",
        )
        feedback.save()
    yield feedback


@pytest.fixture
def jemima_chat(jemima_puddleduck):
    chat = models.Chat(user=jemima_puddleduck)
    chat.save()
    yield chat


@pytest.fixture
def peter_rabbit_prompt(peter_chat):
    prompt = models.Prompt(chat=peter_chat, user_prompt="latest prompt", potentially_sensitive=True)
    prompt.save()
    yield prompt


@pytest.fixture
def multiple_chats_for_user(mrs_tiggywinkle):
    with freeze_time("2020-12-01 12:00:01"):
        chat1 = models.Chat(user=mrs_tiggywinkle)
        chat1.save()
    with freeze_time("2022-10-02 15:06:00"):
        chat2 = models.Chat(user=mrs_tiggywinkle)
        chat2.save()
    yield mrs_tiggywinkle


@pytest.fixture
def mock_request():
    return MagicMock()


@pytest.fixture
def cola_login_view(mock_request):
    cola_login = ColaLoginForceDeclaration()
    cola_login.request = mock_request
    return cola_login


@pytest.fixture
def user_with_no_groups(create_user):
    return create_user("alex@example.gov.uk", "2020-01-01")


@pytest.fixture
def user_with_a_group(create_user):
    user = create_user("brian@example.gov.uk", "2020-01-01")
    user.groups.add(Group.objects.get(name="Data download"))
    return user


@pytest.fixture
def chat_with_complex_characters(create_user):
    user = create_user("complex@example.com", "2020-01-01")
    chat = models.Chat(user=user)
    chat.save()
    prompt1 = models.Prompt(
        chat=chat, user_prompt="Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'"
    )
    prompt1.save()
    prompt2 = models.Prompt(
        chat=chat, user_prompt="Example text with a big list things separated by commas: apple, pear, commas, llamas."
    )
    prompt2.save()
    yield chat


@pytest.fixture
def feedback_with_complex_characters(create_user):
    user = create_user("complex@example.com", "2020-01-01")
    feedback1 = models.Feedback(
        user=user,
        improve_the_service="Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'",
        take_part_in_user_research=False,
        satisfaction="NO_OPINION",
    )
    feedback1.save()
    feedback2 = models.Feedback(
        user=user,
        improve_the_service="Example text with a big list things separated by commas: apple, pear, commas, llamas.",
        take_part_in_user_research=False,
        satisfaction="NO_OPINION",
    )
    feedback2.save()
    all_feedback = models.Feedback.objects.all()
    return list(all_feedback)


@pytest.fixture
def chat_with_unsafe_content(create_user):
    user = create_user("unsafe@example.com", "2020-01-01")
    chat = models.Chat(user=user)
    chat.save()
    prompt1 = models.Prompt(chat=chat, user_prompt="=2+3")
    prompt1.save()
    prompt2 = models.Prompt(chat=chat, user_prompt="@Z1")
    prompt2.save()
    yield chat


@pytest.fixture
def feedback_with_unsafe_content(create_user):
    user = create_user("unsafe@example.com", "2020-01-01")
    feedback1 = models.Feedback(
        user=user,
        improve_the_service="=2+3",
        take_part_in_user_research=False,
        satisfaction="NO_OPINION",
    )
    feedback1.save()
    feedback2 = models.Feedback(
        user=user,
        improve_the_service="@Z1",
        take_part_in_user_research=False,
        satisfaction="NO_OPINION",
    )
    feedback2.save()
    all_feedback = models.Feedback.objects.all()
    yield all_feedback


@pytest.fixture
def simple_chat_prompt(bob):
    with freeze_time("2024-01-01 12:00:01"):
        chat = models.Chat(user=bob)
        chat.save()
        prompt = models.Prompt(
            chat=chat,
            user_prompt="My first prompt",
            ai_response="ChatGPT stuff",
            potentially_sensitive="True",
            user_confirmed_not_sensitive=True,
            user_prompt_moderated=False,
            ai_response_moderated=False,
            cost_input_dollars=3,
            cost_output_dollars=4,
            tokens_input=5,
            tokens_output=6,
        )
        prompt.save()
    yield chat


@pytest.fixture
def simple_feedback(bob):
    with freeze_time("2024-01-01 12:00:01"):
        feedback = models.Feedback(
            user=bob,
            improve_the_service="Suggestions to improve the service",
            take_part_in_user_research=False,
            satisfaction="NO_OPINION",
        )
        feedback.save()
    yield feedback
