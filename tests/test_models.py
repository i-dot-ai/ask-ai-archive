import pytest

from ask_ai.conversation import models


@pytest.mark.django_db
def test_total_spent_dollars(peter_and_bob_chat):
    peter_rabbit = models.User.objects.get(email="peter.rabbit@example.com")
    total = peter_rabbit.total_spent_dollars
    assert total == 2.15, total


@pytest.mark.django_db
def test_is_sensitive(peter_rabbit_prompt):
    prompt = peter_rabbit_prompt
    assert prompt.is_sensitive
    prompt.user_confirmed_not_sensitive = False
    prompt.save()
    assert prompt.is_sensitive
    prompt.user_confirmed_not_sensitive = True
    prompt.save()
    assert not prompt.is_sensitive


@pytest.mark.django_db
def test_assign_features_to_user(user_with_no_groups):
    # general-user doesn't map to any group, no extra permissions
    features = ["general-user", "data-download"]
    user_with_no_groups.assign_features_to_user(features)
    new_groups_for_user = user_with_no_groups.groups.all()
    assert new_groups_for_user.count() == 1
    assert new_groups_for_user.first().name == "Data download"


@pytest.mark.django_db
def test_assign_features_to_user_removes_groups(user_with_a_group):
    features = ["general-user"]
    user_with_a_group.assign_features_to_user(features)
    new_groups_for_user = user_with_a_group.groups.all()
    assert new_groups_for_user.count() == 0
