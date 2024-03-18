from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from . import models


def check_chat_permission(func):
    def wrapper(request, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        if chat_id:
            try:
                chat = models.Chat.objects.get(pk=chat_id)
            except models.Chat.DoesNotExist:
                return render(request, "generic-error.html", {"errors": ["Chat could not be found."]})
            if not (request.user == chat.user):
                return render(request, "generic-error.html", {"errors": ["Chat could not be found."]})
        return func(request, *args, **kwargs)

    return wrapper


def login_required_and_force_declaration(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("login"))
        elif not request.user.completed_declaration:
            return redirect(reverse("declaration"))
        return func(request, *args, **kwargs)

    return wrapper


def check_user_in_data_download_group(func):
    def wrapper(request, *args, **kwargs):
        user = request.user
        user_in_data_download = user.groups.filter(name="Data download").exists()
        if not user_in_data_download:
            raise Http404("Page not found")
        return func(request, *args, **kwargs)

    return wrapper
