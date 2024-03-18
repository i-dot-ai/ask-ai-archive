from django import forms

from ask_ai.conversation import models

REQUIRED_CHECKBOX_ERROR = {"required": "You must agree to this statement"}


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = models.Feedback
        fields = ["improve_the_service", "satisfaction", "take_part_in_user_research"]
        error_messages = {
            "satisfaction": {
                "required": "You must select an option",
            },
            "take_part_in_user_research": {
                "required": "You must select an option",
            },
        }


class DeclarationForm(forms.Form):
    confirm_not_sensitive = forms.BooleanField(required=True, error_messages=REQUIRED_CHECKBOX_ERROR)
    confirm_no_personal_data = forms.BooleanField(required=True, error_messages=REQUIRED_CHECKBOX_ERROR)
    confirm_results_to_be_checked = forms.BooleanField(required=True, error_messages=REQUIRED_CHECKBOX_ERROR)
    confirm_info_retained = forms.BooleanField(required=True, error_messages=REQUIRED_CHECKBOX_ERROR)
