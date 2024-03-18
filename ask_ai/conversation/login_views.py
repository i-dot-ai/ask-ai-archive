from automatilib.cola.views import ColaLogin
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from ask_ai.conversation.models import User


@require_http_methods(["GET"])
def login_to_cola_view(request):
    if request.user.id:
        return redirect(reverse("homepage"))
    cola_url = settings.COLA_LOGIN_URL
    return render(request, "auth/login.html", {"cola_url": cola_url})


class ColaLoginForceDeclaration(ColaLogin):
    def post_login(self):
        user = self.request.user
        user.completed_declaration = False  # Reset on each login
        user.save()

    def handle_user_jwt_details(self, user: User, token_payload: dict) -> None:
        features = token_payload.get("custom:features", "").split(",")
        user.assign_features_to_user(features)
