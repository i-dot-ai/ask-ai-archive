from unittest.mock import MagicMock

import pytest


@pytest.mark.django_db
def test_post_login_resets_completed_declaration(cola_login_view):
    mock_user = MagicMock()
    mock_user.completed_declaration = True
    cola_login_view.request.user = mock_user
    assert cola_login_view.request.user.completed_declaration
    cola_login_view.post_login()
    assert cola_login_view.request.user.completed_declaration is False
