import datetime
import json

from defusedcsv import csv
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from . import models, permissions

PROMPT_FIELDNAME_MAPPING = {
    "created_at": "created_at",
    "chat__user__id": "user_id",
    "chat_id": "chat_id",
    "id": "prompt_id",
    "user_prompt": "prompt",
    "ai_response": "ai_response",
    "potentially_sensitive": "flagged_as_potentially_sensitive",
    "user_confirmed_not_sensitive": "user_confirmed_not_sensitive",
    "user_prompt_moderated": "prompt_moderated",
    "ai_response_moderated": "ai_response_moderated",
    "api_call_error": "api_error",
    "tokens_input": "tokens_input",
    "tokens_output": "tokens_output",
    "cost_input_dollars": "cost_input_dollars",
    "cost_output_dollars": "cost_output_dollars",
}

FEEDBACK_FIELDNAME_MAPPING = {
    "created_at": "created_at",
    "user_id": "feedback_user_id",
    "satisfaction": "satisfaction",
    "id": "feedback_id",
    "improve_the_service": "improve_the_service",
    "take_part_in_user_research": "take_part_in_user_research",
}


def get_all_prompt_data_for_download():
    qs = models.Prompt.objects.order_by("chat__id", "created_at")
    annotations = {
        display_name: F(db_name)
        for db_name, display_name in PROMPT_FIELDNAME_MAPPING.items()
        if db_name != display_name
    }
    qs = qs.annotate(**annotations)
    data = qs.values(*PROMPT_FIELDNAME_MAPPING.values())
    return data


def get_prompt_headers_for_download(filetype: str) -> dict:
    # filetype: "csv" or "json"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}-ask-ai-chat-data.{filetype}"
    headers = {
        "Content-Type": "text/{filetype}",
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return headers


def get_all_feedback_data_for_download():
    qs = models.Feedback.objects.order_by("created_at")
    annotations = {
        display_name: F(db_name)
        for db_name, display_name in FEEDBACK_FIELDNAME_MAPPING.items()
        if db_name != display_name
    }
    qs = qs.annotate(**annotations)
    data = qs.values(*FEEDBACK_FIELDNAME_MAPPING.values())
    return data


def get_feedback_headers_for_download(filetype: str) -> dict:
    # filetype: "csv" or "json"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}-ask-ai-feedback-data.{filetype}"
    headers = {
        "Content-Type": "text/{filetype}",
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return headers


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def prompt_data_download_view(request):
    if "csv" in request.GET:
        return prompt_data_download_csv_view(request)
    elif "json" in request.GET:
        return prompt_data_download_json_view(request)
    return render(request, "data-download.html")


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def prompt_data_download_csv_view(request):
    data = get_all_prompt_data_for_download()
    headers = get_prompt_headers_for_download("csv")
    response = HttpResponse(headers=headers)
    writer = csv.DictWriter(
        response, fieldnames=PROMPT_FIELDNAME_MAPPING.values(), extrasaction="ignore", quoting=csv.QUOTE_ALL
    )
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return response


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def prompt_data_download_json_view(request):
    data = get_all_prompt_data_for_download()
    data = list(data)
    headers = get_prompt_headers_for_download("json")
    response = HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), headers=headers)
    return response


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def feedback_data_download_view(request):
    if "csv" in request.GET:
        return feedback_data_download_csv_view(request)
    elif "json" in request.GET:
        return feedback_data_download_json_view(request)
    return render(request, "feedback-download.html")


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def feedback_data_download_csv_view(request):
    data = get_all_feedback_data_for_download()
    headers = get_feedback_headers_for_download("csv")
    response = HttpResponse(headers=headers)
    writer = csv.DictWriter(
        response, fieldnames=FEEDBACK_FIELDNAME_MAPPING.values(), extrasaction="ignore", quoting=csv.QUOTE_ALL
    )
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return response


@permissions.login_required_and_force_declaration
@permissions.check_user_in_data_download_group
@require_http_methods(["GET"])
def feedback_data_download_json_view(request):
    data = get_all_feedback_data_for_download()
    data = list(data)
    headers = get_feedback_headers_for_download("json")
    response = HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), headers=headers)
    return response
