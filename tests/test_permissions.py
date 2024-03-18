"""
Tests to ensure can't access certain views if you don't have the right permissions.
Initial tests check all URLs and deliberate exclude some - this is so we ensure new
URLs get tested. You will have to be explicit about URLs that don't need to be tested (for access).
"""
import pytest
from django.urls import reverse

from ask_ai import urls

from . import utils

# Explicitly excluding URLs if they need different tests
# This is to ensure that we don't miss out new URLs
URL_PATTERNS = (
    set(urls.urlpatterns)
    - set(urls.health_urlpatterns)
    - set(urls.cola_urlpatterns)
    - set(urls.admin_urlpatterns)
    - set(urls.data_download_urlpatterns)
)


NAMES_TO_IGNORE = [
    "chat",
    "new-chat",
    "chat-option",
    "chat-sensitivity-check",
    "health",
    "login",
    "index",
    "homepage",
    "privacy",
    "support",
    "accessibility",
    "cookies",
]  # separate tests


VALID_URL_PATTERNS = [url.name for url in URL_PATTERNS if url.name not in NAMES_TO_IGNORE]


@pytest.mark.parametrize("url_pattern", VALID_URL_PATTERNS)
@pytest.mark.django_db
def test_access_urls(client, peter_rabbit, url_pattern):
    url = reverse(url_pattern)
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    response = client.get(url)
    assert response.status_code == 200, response.url


@pytest.mark.parametrize("url_pattern", VALID_URL_PATTERNS)
@pytest.mark.django_db
def test_cant_access_urls(client, url_pattern):
    url = reverse(url_pattern)
    response = client.get(url)
    assert response.status_code == 302, response.status_code
    assert response.url.startswith("/login/"), response.url


@pytest.mark.django_db
def test_can_access_health_url(client):
    response = client.get("/health/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_cant_access_new_chat_url(client):
    response = client.get("/new-chat/")
    assert response.status_code == 404, response.status_code


@pytest.mark.django_db
def test_access_new_chat(client, peter_rabbit):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse("new-chat")
    response = client.get(url, follow=True)  # redirect to the new chat
    assert response.status_code == 200, response.status_code


@pytest.mark.parametrize("url_name", ["chat", "chat-sensitivity-check"])
@pytest.mark.django_db
def test_access_chat(client, peter_rabbit, peter_chat, url_name):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse(url_name, args=(peter_chat.id,))
    response = client.get(url)
    assert response.status_code == 200, response.status_code


@pytest.mark.django_db
def test_access_chat_option(client, peter_rabbit, peter_chat):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse(
        "chat-option",
        args=(
            peter_chat.id,
            "populate-text-box",
        ),
    )
    response = client.get(url)
    assert response.status_code == 200, response.status_code


@pytest.mark.django_db
def test_cant_access_chat_option(client, peter_rabbit, jemima_chat):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse(
        "chat-option",
        args=(
            jemima_chat.id,
            "populate-text-box",
        ),
    )
    response = client.get(url)
    assert response.status_code == 200, response.status_code
    assert "Chat could not be found." in response.content.decode(), response.content.decode()


@pytest.mark.parametrize("url_name", ["chat", "chat-sensitivity-check"])
@pytest.mark.django_db
def test_cant_access_other_user_chat(client, peter_rabbit, jemima_chat, url_name):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse(url_name, args=(jemima_chat.id,))
    response = client.get(url)
    assert response.status_code == 200, response.status_code
    assert "Chat could not be found." in response.content.decode(), response.content.decode()


@pytest.mark.parametrize("url_name", ["chat", "chat-sensitivity-check"])
@pytest.mark.django_db
def test_cant_access_chat(client, jemima_chat, url_name):
    url = reverse(url_name, args=(jemima_chat.id,))
    response = client.get(url)
    assert response.status_code == 302, response.status_code


@pytest.mark.parametrize("url_pattern", ["privacy", "support", "accessibility", "cookies"])
@pytest.mark.django_db
def test_access_public_urls(client, url_pattern):
    url = reverse(url_pattern)
    response = client.get(url)
    assert response.status_code == 200, response.url


@pytest.mark.parametrize("url_name", ["data-download"])
@pytest.mark.django_db
def test_data_download_logged_out(client, url_name):
    url = reverse(url_name)
    response = client.get(url)
    assert response.status_code == 302, response.status_code


@pytest.mark.parametrize("url_name", ["data-download"])
@pytest.mark.django_db
def test_data_download_shouldnt_access(client, url_name, peter_rabbit):
    client.force_login(peter_rabbit)
    utils.complete_declaration(client)
    url = reverse(url_name)
    response = client.get(url)
    assert response.status_code == 404, response.status_code


@pytest.mark.parametrize("url_name", ["data-download"])
@pytest.mark.django_db
def test_data_download_can_access(client, url_name, bob):
    client.force_login(bob)
    utils.complete_declaration(client)
    url = reverse(url_name)
    response = client.get(url, follow=True)
    assert response.status_code == 200, response.status_code
