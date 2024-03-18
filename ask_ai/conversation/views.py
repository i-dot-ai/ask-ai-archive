import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

import ask_ai.conversation.constants

from . import chat_gpt, forms, models, permissions, sensitivity_check, utils

ACCEPT_OPTIONS = (
    {
        "name": "confirm_not_sensitive",
        "label": "I will not input information that is <strong>classified</strong>, <strong>sensitive</strong> or <strong>reveals the intent of government</strong> (that may not be in the public domain) into Ask AI.",  # noqa
    },
    {
        "name": "confirm_no_personal_data",
        "label": "I will not input <strong>personal data</strong> into Ask AI as defined under the Data Protection Act (2018).",
    },
    {
        "name": "confirm_results_to_be_checked",
        "label": "I understand that the outputs from Ask AI are <strong>susceptible to bias and misinformation</strong> and they need to be checked and cited appropriately.",
    },
    {
        "name": "confirm_info_retained",
        "label": "I understand that the information I input and the replies received will be retained by the Cabinet Office for auditing purposes.",  # noqa
    },
)

POPULATE_TEXT_BOX = "populate-text-box"


@permissions.login_required_and_force_declaration
@require_http_methods(["GET"])
def index_view(request):
    return redirect(reverse("new-chat"))


@login_required
@require_http_methods(["GET", "POST"])
def declaration_view(request):
    errors = {}
    data = {}
    form = forms.DeclarationForm()
    if request.POST:
        form = forms.DeclarationForm(request.POST)
        if form.is_valid():
            user = request.user
            user.completed_declaration = True
            user.save()
            return redirect(reverse("new-chat"))
        data = request.POST
        errors = utils.get_form_errors_as_strings(form.errors)
    return render(
        request,
        template_name="declaration.html",
        context={"form": form, "options": ACCEPT_OPTIONS, "errors": errors, "data": data},
    )


def get_chat(user, chat_id):
    chat_created = False
    if not chat_id:
        chat = models.Chat(user=user)
        chat.save()
        chat_created = True
    else:
        chat = models.Chat.objects.get(id=chat_id)
    return chat, chat_created


def get_past_chats_for_user(user):
    today = datetime.date.today()
    today_chats = utils.get_chats_for_user_created_between(user, start_date=today)
    previous_chats = utils.get_chats_for_user_created_between(
        user,
        start_date=None,
        end_date=(today - datetime.timedelta(days=1)),
    )
    past_chats = {"today": today_chats, "previous": previous_chats}
    return past_chats


@permissions.login_required_and_force_declaration
@permissions.check_chat_permission
@require_http_methods(["GET", "POST"])
def chat_view(request, chat_id=None, option=None):
    # Possible options: POPULATE_TEXT_BOX
    # In some cases, populate the text box with previous prompt to enable editing
    errors = {}
    data = {}
    past_chats = get_past_chats_for_user(request.user)
    llm_model = models.Prompt.LLMModels.GPT35_TURBO_0125
    if chat_id:
        prompts_list = models.Prompt.objects.filter(chat__id=chat_id).order_by("created_at")
        api_error = prompts_list.last().api_call_error
        if option == POPULATE_TEXT_BOX:  # only do this when there is a chat
            latest_prompt = models.Prompt.objects.filter(chat__id=chat_id).order_by("created_at").last()
            data = {"user_prompt": latest_prompt.user_prompt}
    else:
        prompts_list = models.Prompt.objects.none()
        api_error = False
    if request.POST:
        input_text = request.POST.dict().get("user_prompt")
        # Check for length before saving - don't save if only prompt too long
        prompt_too_long = chat_gpt.is_prompt_over_token_limit(
            input_text, llm_model, buffer=ask_ai.conversation.constants.BUFFER_TOKENS
        )
        if not prompt_too_long:
            try:
                chat, _ = get_chat(request.user, chat_id)
                chat_id = chat.id
                prompt = models.Prompt(chat=chat, llm_model=llm_model, user_prompt=input_text)
                prompt.save()
                input_text = prompt.user_prompt
                moderated = chat_gpt.chat_gpt_moderated(input_text)
                if moderated:
                    prompt.user_prompt_moderated = True
                    prompt.save()
                    return redirect(reverse("chat", args=(chat_id,)))
                else:
                    potentially_sensitive = sensitivity_check.is_text_potentially_sensitive(input_text)
                    prompt.potentially_sensitive = potentially_sensitive
                    prompt.save()
                    if potentially_sensitive:
                        return redirect(reverse("chat-sensitivity-check", args=(chat_id,)))
                    chat_gpt_inputs = chat_gpt.get_chat_gpt_inputs(prompt.chat, llm_model)
                    prompt = chat_gpt.submit_valid_chat_to_chatgpt35(prompt, chat_gpt_inputs)
                    return redirect(reverse("chat", args=(chat_id,)))
            except chat_gpt.OPEN_AI_API_ERRORS:
                prompt.api_call_error = True
                prompt.save()
                return redirect(reverse("chat-option", args=(chat_id, POPULATE_TEXT_BOX)))
        else:
            errors[
                "user_prompt"
            ] = "This query is too long for ChatGPT, please shorten your query or submit two separate queries"
            data = {"user_prompt": input_text}
    return render(
        request,
        template_name="chat.html",
        context={
            "prompts": prompts_list,
            "errors": errors,
            "past_chats": past_chats,
            "api_error": api_error,
            "data": data,
        },
    )


@permissions.login_required_and_force_declaration
@permissions.check_chat_permission
@require_http_methods(["GET", "POST"])
def check_sensitivity_view(request, chat_id):
    data = {}
    api_error = False
    chat = models.Chat.objects.get(id=chat_id)
    past_chats = get_past_chats_for_user(request.user)
    all_prompts = models.Prompt.objects.filter(chat=chat).order_by("created_at")
    latest_prompt = all_prompts.last()
    existing_prompts = all_prompts.exclude(id=latest_prompt.id).order_by("created_at")
    llm_model = models.Prompt.LLMModels.GPT35_TURBO_0125
    if request.POST:
        if "not-sensitive" in request.POST.dict():
            latest_prompt.user_confirmed_not_sensitive = True
            latest_prompt.save()
            try:
                chat_gpt_inputs = chat_gpt.get_chat_gpt_inputs(latest_prompt.chat, llm_model)
                latest_prompt = chat_gpt.submit_valid_chat_to_chatgpt35(latest_prompt, chat_gpt_inputs)
            except chat_gpt.OPEN_AI_API_ERRORS:
                latest_prompt.api_call_error = True
                latest_prompt.save()
                data = {"user_prompt": latest_prompt.user_prompt}
            return redirect(reverse("chat", args=(chat.id,)))
        return redirect(
            reverse(
                "chat-option",
                args=(
                    chat.id,
                    POPULATE_TEXT_BOX,
                ),
            )
        )  # populate text box for editing
    return render(
        request,
        template_name="chat.html",
        context={
            "prompts": existing_prompts,
            "errors": {},
            "past_chats": past_chats,
            "api_error": api_error,
            "sensitive_prompt": latest_prompt,
            "data": data,
        },
    )


@permissions.login_required_and_force_declaration
@require_http_methods(["GET"])
def guidance_view(request):
    return render(request, "guidance.html")


@require_http_methods(["GET"])
def privacy_view(request):
    return render(request, "privacy.html")


@require_http_methods(["GET"])
def support_view(request):
    return render(request, "support.html")


@require_http_methods(["GET"])
def accessibility_view(request):
    return render(request, "accessibility.html")


@require_http_methods(["GET"])
def cookies_view(request):
    return render(request, "cookies.html")


@permissions.login_required_and_force_declaration
@require_http_methods(["GET", "POST"])
def feedback_view(request):
    errors = {}
    data = {}
    form = forms.FeedbackForm()
    if request.method == "POST":
        form = forms.FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return redirect(reverse("new-chat"))
        errors = utils.get_form_errors_as_strings(form.errors)
        data = request.POST
    return render(
        request,
        "feedback.html",
        {
            "form": form,
            "errors": errors,
            "data": data,
            "satisfaction_choices": models.Feedback.Satisfaction.choices,
            "ur_choices": models.Feedback.YES_NO_CHOICES,
        },
    )
