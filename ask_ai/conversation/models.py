import uuid

from automatilib.core.models import IDotAiUser
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.enums import TextChoices


FEATURES_TO_GROUP_MAP = {"data-download": "Data download"}


class UUIDPrimaryKeyBase(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class TimeStampedModel(UUIDPrimaryKeyBase):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]


class User(IDotAiUser):
    # Resets every login, user must complete declaration every time
    completed_declaration = models.BooleanField(default=False, blank=False, null=False)

    def assign_features_to_user(self, features: list[str]):
        group_names = set(
            FEATURES_TO_GROUP_MAP.get(feature) for feature in features if feature in FEATURES_TO_GROUP_MAP.keys()
        )
        groups = Group.objects.filter(name__in=group_names)
        # User permissions managed in COLA via features - also remove permissions no longer needed
        self.groups.set(groups)
        self.save()

    @property
    def total_spent_dollars(self):
        chats_for_user = Chat.objects.filter(user=self)
        all_prompts_for_user = Prompt.objects.filter(chat__in=chats_for_user)
        total_input_costs = all_prompts_for_user.aggregate(total=models.Sum("cost_input_dollars"))["total"]
        total_output_costs = all_prompts_for_user.aggregate(total=models.Sum("cost_output_dollars"))["total"]
        overall_total = total_input_costs + total_output_costs
        return overall_total


class Chat(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Prompt(TimeStampedModel):
    class LLMModels(TextChoices):
        GPT35_TURBO = "GPT35_TURBO", "gpt-3.5-turbo"
        GPT35_TURBO_1106 = "GPT35_TURBO_1106", "gpt-3.5-turbo-1106"
        GPT35_TURBO_0125 = "GPT35_TURBO_0125", "gpt-3.5-turbo-0125"

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    llm_model = models.CharField(max_length=32, choices=LLMModels.choices, blank=True, default="")
    user_prompt = models.TextField(blank=True, default="")
    ai_response = models.TextField(blank=True, default="")
    potentially_sensitive = models.BooleanField(default=False)
    user_confirmed_not_sensitive = models.BooleanField(default=False)
    user_prompt_moderated = models.BooleanField(default=False)
    ai_response_moderated = models.BooleanField(default=False)
    api_call_error = models.BooleanField(default=False)
    cost_input_dollars = models.FloatField(default=0)
    cost_output_dollars = models.FloatField(default=0)
    tokens_input = models.PositiveSmallIntegerField(null=True)
    tokens_output = models.PositiveSmallIntegerField(null=True)

    @property
    def is_sensitive(self):
        # Assume sensitive unless specifically confirmed by user
        return self.potentially_sensitive and not self.user_confirmed_not_sensitive


class Feedback(TimeStampedModel, UUIDPrimaryKeyBase):
    class Satisfaction(TextChoices):
        VERY_DISSATISFIED = "VERY_DISSATISFIED", "Very dissatisfied"
        DISSATISFIED = "DISSATISFIED", "Dissatisfied"
        NO_OPINION = "NO_OPINION", "No opinion"
        SATISFIED = "SATISFIED", "Satisfied"
        VERY_SATISFIED = "VERY_SATISFIED", "Very satisfied"

    YES = True
    NO = False
    YES_NO_CHOICES = [(YES, "Yes"), (NO, "No")]

    satisfaction = models.CharField(max_length=254, choices=Satisfaction.choices)
    improve_the_service = models.TextField(blank=True)
    take_part_in_user_research = models.BooleanField(blank=False, choices=YES_NO_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
