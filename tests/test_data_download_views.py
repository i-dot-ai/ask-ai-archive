import csv
import io
import json

import pytest
from django.urls import reverse

from ask_ai.conversation import models

from . import utils


@pytest.mark.django_db
def test_prompt_data_download_csv(client, bob, peter_chat):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    first_row = next(reader)
    assert first_row == [
        "created_at",
        "user_id",
        "chat_id",
        "prompt_id",
        "prompt",
        "ai_response",
        "flagged_as_potentially_sensitive",
        "user_confirmed_not_sensitive",
        "prompt_moderated",
        "ai_response_moderated",
        "api_error",
        "tokens_input",
        "tokens_output",
        "cost_input_dollars",
        "cost_output_dollars",
    ]
    second_row = next(reader)
    assert "What is the capital of Spain?" in second_row, second_row
    assert "2024-01-01 12:00:01+00:00" in second_row, second_row


@pytest.mark.django_db
def test_prompt_data_download_csv_no_data(client, bob):
    # Though realistically, this case won't happen on prod as there
    # is already data there
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    first_row = next(reader, None)
    assert first_row == [
        "created_at",
        "user_id",
        "chat_id",
        "prompt_id",
        "prompt",
        "ai_response",
        "flagged_as_potentially_sensitive",
        "user_confirmed_not_sensitive",
        "prompt_moderated",
        "ai_response_moderated",
        "api_error",
        "tokens_input",
        "tokens_output",
        "cost_input_dollars",
        "cost_output_dollars",
    ]
    second_row = next(reader, None)
    assert not second_row


@pytest.mark.django_db
def test_prompt_formatting_csv_download(client, bob, chat_with_complex_characters):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    headers_row = next(reader)
    assert "user_id" in headers_row
    second_row = next(reader)
    assert (
        second_row[4] == "Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'"
    ), second_row
    third_row = next(reader)
    assert (
        third_row[4] == "Example text with a big list things separated by commas: apple, pear, commas, llamas."
    ), third_row


@pytest.mark.django_db
def test_prompt_csv_injection_data_download(client, bob, chat_with_unsafe_content):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    headers_row = next(reader)
    assert "prompt" in headers_row
    second_row = next(reader)
    assert second_row[4] == "'=2+3", second_row


@pytest.mark.django_db
def test_prompt_json_download(client, bob, chat_with_complex_characters, peter_chat):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-json"), {"json": ""})
    assert response.status_code == 200
    all_data = json.loads(response.content)
    assert len(all_data) > 3
    first_dictionary = all_data[0]
    fieldnames = {
        "created_at",
        "user_id",
        "chat_id",
        "prompt_id",
        "prompt",
        "ai_response",
        "flagged_as_potentially_sensitive",
        "user_confirmed_not_sensitive",
        "prompt_moderated",
        "ai_response_moderated",
        "api_error",
        "tokens_input",
        "tokens_output",
        "cost_input_dollars",
        "cost_output_dollars",
    }
    assert set(first_dictionary.keys()) == fieldnames
    user_prompts = [prompt["prompt"] for prompt in all_data]
    p = "Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'"
    assert p in user_prompts


@pytest.mark.django_db
def test_prompt_json_download_again(client, bob, simple_chat_prompt):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("data-download-json"), {"json": ""})
    assert response.status_code == 200
    bob = models.User.objects.get(email="bob@example.com")
    chat = models.Chat.objects.get(user=bob)
    prompt = models.Prompt.objects.get(chat=chat)
    all_data = json.loads(response.content)
    actual_values = all_data[0]
    expected_values = {
        "created_at": "2024-01-01T12:00:01Z",
        "user_id": str(bob.id),
        "chat_id": str(chat.id),
        "prompt_id": str(prompt.id),
        "prompt": "My first prompt",
        "ai_response": "ChatGPT stuff",
        "flagged_as_potentially_sensitive": True,
        "user_confirmed_not_sensitive": True,
        "prompt_moderated": False,
        "ai_response_moderated": False,
        "api_error": False,
        "tokens_input": 5,
        "tokens_output": 6,
        "cost_input_dollars": 3,
        "cost_output_dollars": 4,
    }
    assert expected_values == actual_values


@pytest.mark.django_db
def test_feedback_data_download_csv(client, bob, peter_feedback):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    first_row = next(reader)
    assert first_row == [
        "created_at",
        "feedback_user_id",
        "satisfaction",
        "feedback_id",
        "improve_the_service",
        "take_part_in_user_research",
    ]
    second_row = next(reader)
    assert "Something that will improve the service" in second_row, second_row
    assert "2024-01-01 12:00:01+00:00" in second_row, second_row


@pytest.mark.django_db
def test_feedback_data_download_csv_no_data(client, bob):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    first_row = next(reader, None)
    assert first_row == [
        "created_at",
        "feedback_user_id",
        "satisfaction",
        "feedback_id",
        "improve_the_service",
        "take_part_in_user_research",
    ]
    second_row = next(reader, None)
    assert not second_row


@pytest.mark.django_db
def test_feedback_formatting_csv_download(client, bob, feedback_with_complex_characters):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    headers_row = next(reader)
    assert "feedback_user_id" in headers_row
    second_row = next(reader)
    assert (
        second_row[4] == "Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'"
    ), second_row
    third_row = next(reader)
    assert (
        third_row[4] == "Example text with a big list things separated by commas: apple, pear, commas, llamas."
    ), third_row


@pytest.mark.django_db
def test_feedback_csv_injection_data_download(client, bob, feedback_with_unsafe_content):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-csv"), {"csv": ""})
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8"))
    reader = csv.reader(csv_file)
    headers_row = next(reader)
    assert "improve_the_service" in headers_row
    second_row = next(reader)
    assert second_row[4] == "'=2+3", second_row


@pytest.mark.django_db
def test_feedback_json_download(client, bob, feedback_with_complex_characters, peter_chat):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-json"), {"json": ""})
    assert response.status_code == 200
    all_data = json.loads(response.content)
    assert len(all_data) > 1
    first_dictionary = all_data[0]
    fieldnames = {
        "created_at",
        "satisfaction",
        "improve_the_service",
        "take_part_in_user_research",
        "feedback_user_id",
        "feedback_id",
    }
    assert set(first_dictionary.keys()) == fieldnames
    feedbacks = [feedback["improve_the_service"] for feedback in all_data]
    p = "Example text with commas, \nnew lines\n and \"quotations!\" and 'single quotes'"
    assert p in feedbacks


@pytest.mark.django_db
def test_feedback_json_download_again(client, bob, simple_feedback):
    client.force_login(bob)
    utils.complete_declaration(client)
    response = client.get(reverse("feedback-download-json"), {"json": ""})
    assert response.status_code == 200
    bob = models.User.objects.get(email="bob@example.com")
    feedback = models.Feedback.objects.get(user=bob)
    all_data = json.loads(response.content)
    actual_values = all_data[0]
    expected_values = {
        "created_at": "2024-01-01T12:00:01Z",
        "feedback_user_id": str(bob.id),
        "feedback_id": str(feedback.id),
        "satisfaction": "NO_OPINION",
        "improve_the_service": "Suggestions to improve the service",
        "take_part_in_user_research": False,
    }
    assert expected_values == actual_values
