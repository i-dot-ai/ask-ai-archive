import pytest
from django.urls import reverse

from ask_ai.conversation import models
from tests.test_chat_gpt import (
    mock_chat_gpt_moderation_false,
    mock_chat_gpt_moderation_true,
    mock_get_gpt35_turbo_response,
)

from . import utils


@pytest.mark.django_db
def test_declaration_view_get(peter_rabbit, client):
    client.force_login(peter_rabbit)
    response = client.get("/declaration/")
    assert response.status_code == 200, response.status_code
    assert "Declaration" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_declaration_view_validation_error(peter_rabbit, client):
    client.force_login(peter_rabbit)
    response = client.post("/declaration/", data={"confirm_not_sensitive": True})
    assert response.status_code == 200, response.status_code
    assert "You must agree to this statement" in response.content.decode("utf-8")
    assert "Declaration" in response.content.decode("utf-8")
    user = models.User.objects.get(email="peter.rabbit@example.com")
    assert not user.completed_declaration


@pytest.mark.django_db
def test_declaration_view_post_success(peter_rabbit, client):
    client.force_login(peter_rabbit)
    response = client.post(
        "/declaration/",
        data={
            "confirm_not_sensitive": True,
            "confirm_info_retained": True,
            "confirm_results_to_be_checked": True,
            "confirm_no_personal_data": True,
        },
    )
    assert response.status_code == 302, response.status_code
    assert response.url == reverse("new-chat")
    user = models.User.objects.get(email="peter.rabbit@example.com")
    assert user.completed_declaration


@pytest.mark.django_db
def test_chat_view_post_moderated(mrs_tiggywinkle, mrs_tiggywinkle_chat, client, monkeypatch):
    client.force_login(mrs_tiggywinkle)
    utils.complete_declaration(client)
    chat_id = mrs_tiggywinkle_chat[0].id
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_true)
    response = client.post(reverse("chat", args=(chat_id,)), {"user_prompt": "Dodgy chat to be moderated"})
    assert response.status_code == 302, response.status_code
    response = client.get(response.url)
    assert "been moderated" in response.content.decode("utf-8")
    assert response.status_code == 200
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert latest_prompt.user_prompt.startswith("Dodgy chat"), latest_prompt.user_prompt
    assert latest_prompt.user_prompt_moderated, latest_prompt.user_prompt_moderated


@pytest.mark.django_db
def test_chat_view_post_sensitive(mrs_tiggywinkle, mrs_tiggywinkle_chat, client, monkeypatch):
    client.force_login(mrs_tiggywinkle)
    utils.complete_declaration(client)
    chat_id = mrs_tiggywinkle_chat[0].id
    fake_prompt_text = "Fake sensitive prompt 0131 678766"
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    response = client.post(reverse("chat", args=(chat_id,)), {"user_prompt": fake_prompt_text})
    assert response.status_code == 302, response.status_code  # redirect for user to confirm/deny if sensitive
    assert response.url == reverse("chat-sensitivity-check", args=(chat_id,)), response.url
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert latest_prompt.user_prompt.startswith("Fake sensitive prompt"), latest_prompt.user_prompt
    assert not latest_prompt.user_prompt_moderated, latest_prompt.user_prompt_moderated
    assert latest_prompt.potentially_sensitive, latest_prompt.potentially_sensitive
    response = client.get(response.url)
    assert "I confirm I want to send this to ChatGPT" in response.content.decode(
        "utf-8"
    )  # Button text that should display
    response = client.post(
        reverse("chat-sensitivity-check", args=(chat_id,)), {"sensitive": [""]}
    )  # Confirm it is sensitive
    response = client.get(response.url)  # Should redirect to "chat-option"
    content = response.content.decode("utf-8")
    # should appear as historic query and prepopulated in text box
    assert content.count(fake_prompt_text) == 2, content.count(fake_prompt_text)
    assert not latest_prompt.user_confirmed_not_sensitive  # This was actually sensitive


@pytest.mark.django_db
def test_chat_view_post_potentially_sensitive(mrs_tiggywinkle, mrs_tiggywinkle_chat, client, monkeypatch):
    client.force_login(mrs_tiggywinkle)
    utils.complete_declaration(client)
    chat_id = mrs_tiggywinkle_chat[0].id
    fake_prompt_text = "Not really sensitive prompt 0131 678766"
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    response = client.post(reverse("chat", args=(chat_id,)), {"user_prompt": fake_prompt_text})
    assert response.status_code == 302, response.status_code  # redirect for user to confirm/deny if sensitive
    assert response.url == reverse("chat-sensitivity-check", args=(chat_id,)), response.url
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert latest_prompt.user_prompt.startswith("Not really sensitive prompt"), latest_prompt.user_prompt
    assert not latest_prompt.user_prompt_moderated, latest_prompt.user_prompt_moderated
    assert latest_prompt.potentially_sensitive, latest_prompt.potentially_sensitive
    url = response.url
    response = client.get(url)
    assert "I confirm I want to send this to ChatGPT" in response.content.decode()
    monkeypatch.setattr("ask_ai.conversation.chat_gpt.get_gpt35_turbo_response", mock_get_gpt35_turbo_response)
    response = client.post(url, {"not-sensitive": [""]})  # Confirm it is not sensitive
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert latest_prompt.user_confirmed_not_sensitive


@pytest.mark.django_db
def test_chat_view_post_too_long(mrs_tiggywinkle, mrs_tiggywinkle_chat, client, monkeypatch):
    client.force_login(mrs_tiggywinkle)
    utils.complete_declaration(client)
    chat_id = mrs_tiggywinkle_chat[0].id
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    response = client.post(reverse("chat", args=(chat_id,)), {"user_prompt": "Too long" * 5000})
    assert response.status_code == 200, response.status_code
    assert "This query is too long" in response.content.decode("utf-8")  # error message displays
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert not latest_prompt.user_prompt.startswith("Too long")  # Shouldn't save the too long prompt
    assert "Too long" in response.content.decode("utf-8")  # It should be pre-populated in the chat box


@pytest.mark.django_db
def test_chat_view_post_ok(mrs_tiggywinkle, mrs_tiggywinkle_chat, client, monkeypatch):
    client.force_login(mrs_tiggywinkle)
    utils.complete_declaration(client)
    chat_id = mrs_tiggywinkle_chat[0].id
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    monkeypatch.setattr("ask_ai.conversation.chat_gpt.get_gpt35_turbo_response", mock_get_gpt35_turbo_response)
    response = client.post(reverse("chat", args=(chat_id,)), {"user_prompt": "This prompt is acceptable"})
    assert response.status_code == 302, response.status_code
    response = client.get(response.url)
    assert (
        "What would you like to ask?" not in response.content.decode()
    )  # Question should only be displayed on the first query
    latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("modified_at").last()
    assert latest_prompt.user_prompt.startswith("This prompt is acceptable")
    assert latest_prompt.ai_response.startswith("Mocked response")
    assert not latest_prompt.potentially_sensitive
    assert latest_prompt.tokens_input == 57
    assert latest_prompt.tokens_output == 17


@pytest.mark.django_db
def test_feedback(peter_rabbit, client):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    response = client.post(
        reverse("feedback"),
        {
            "improve_the_service": "Here are my improvements",
            "satisfaction": "SATISFIED",
            "take_part_in_user_research": True,
        },
    )
    assert response.status_code == 302, response.status_code
    assert response.url == reverse("new-chat"), response.url
    latest_feedback = models.Feedback.objects.filter(user=peter_rabbit).order_by("created_at").last()
    assert latest_feedback.improve_the_service == "Here are my improvements", latest_feedback.improve_the_service
    assert latest_feedback.satisfaction == "SATISFIED", latest_feedback.satisfaction
    assert latest_feedback.take_part_in_user_research, latest_feedback.take_part_in_user_research


@pytest.mark.django_db
def test_feedback_incomplete(peter_rabbit, client):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    response = client.post(
        reverse("feedback"), {"improve_the_service": "Here are my improvements", "take_part_in_user_research": False}
    )
    assert "You must select an option" in response.content.decode("utf-8")  # Error when satisfaction not selected


@pytest.mark.django_db
def test_chat_intro_question(alice, client):
    client.force_login(alice)
    utils.complete_declaration(client)
    response = client.get(reverse("new-chat"))
    assert response.status_code == 200, response.status_code
    assert "What would you like to ask?" in response.content.decode()


@pytest.mark.django_db
def test_chat_too_many_tokens_prompt(alice, client):
    client.force_login(alice)
    utils.complete_declaration(client)
    response = client.get(reverse("new-chat"))
    assert response.status_code == 200, response.status_code
    response = client.post(reverse("new-chat"), {"user_prompt": "This prompt is way too long" * 4000})
    assert "This query is too long for ChatGPT" in response.content.decode()


@pytest.mark.django_db
def test_create_chat(alice, client, monkeypatch):
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    monkeypatch.setattr("ask_ai.conversation.chat_gpt.get_gpt35_turbo_response", mock_get_gpt35_turbo_response)
    initial_number_chats = models.Chat.objects.filter(user=alice).count()
    client.force_login(alice)
    alice.completed_declaration = True
    alice.save()
    client.get(reverse("new-chat"))
    new_number_chats = models.Chat.objects.filter(user=alice).count()
    assert initial_number_chats == new_number_chats, new_number_chats
    client.post(reverse("new-chat"), {"user_prompt": "My prompt"})
    new_number_chats = models.Chat.objects.filter(user=alice).count()
    assert new_number_chats > initial_number_chats, new_number_chats
