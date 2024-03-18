from automatilib.cola.views import ColaLogout
from django.contrib import admin
from django.urls import include, path

from ask_ai.conversation import data_download_views, login_views, views
from ask_ai.hosting_environment import HostingEnvironment

admin_urlpatterns = [
    path("admin/", admin.site.urls),
]

health_urlpatterns = [
    path("health/", include("health_check.urls")),
]

other_urlpatterns = [
    path("", views.index_view, name="index"),
    path("home/", views.index_view, name="homepage"),
    path("declaration/", views.declaration_view, name="declaration"),
    path("chat/", views.chat_view, name="new-chat"),
    path("chat/<uuid:chat_id>/", views.chat_view, name="chat"),
    path("chat/<uuid:chat_id>/<str:option>/", views.chat_view, name="chat-option"),
    path("chat-sensitivity-check/<uuid:chat_id>/", views.check_sensitivity_view, name="chat-sensitivity-check"),
    path("guidance/", views.guidance_view, name="guidance"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("support/", views.support_view, name="support"),
    path("accessibility/", views.accessibility_view, name="accessibility"),
    path("cookies/", views.cookies_view, name="cookies"),
    path("feedback/", views.feedback_view, name="feedback"),
]

data_download_urlpatterns = [
    path("data-download/", data_download_views.prompt_data_download_view, name="data-download"),
    path("data-download-csv/", data_download_views.prompt_data_download_csv_view, name="data-download-csv"),
    path("data-download-json/", data_download_views.prompt_data_download_json_view, name="data-download-json"),
    path("feedback-download/", data_download_views.feedback_data_download_view, name="feedback-download"),
    path("feedback-download-csv/", data_download_views.feedback_data_download_csv_view, name="feedback-download-csv"),
    path(
        "feedback-download-json/", data_download_views.feedback_data_download_json_view, name="feedback-download-json"
    ),
]

cola_urlpatterns = [
    path("login/", login_views.login_to_cola_view, name="login"),
    path("post-login/", login_views.ColaLoginForceDeclaration.as_view(), name="post-login"),
    path("logout/", ColaLogout.as_view(), name="logout"),
]

urlpatterns = other_urlpatterns + data_download_urlpatterns + cola_urlpatterns + health_urlpatterns

if HostingEnvironment.is_local():
    urlpatterns = urlpatterns + admin_urlpatterns
