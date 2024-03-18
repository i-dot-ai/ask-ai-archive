"""
These functions call the ChatGPT API.

At the moment we are using GPT3.5 turbo model.
When we extend this, functions will need to be generalised and amended -
inputs/outputs may be in different formats.
"""
import openai
import tiktoken
from django.conf import settings

from ask_ai.conversation.constants import BUFFER_TOKENS, TOKEN_LIMITS
from ask_ai.conversation.models import Chat, Prompt

from . import constants, utils

openai.api_key = settings.OPENAI_KEY

# These are errors we want to catch as solution is just to retry
# Others we probably want to be alerted about
OPEN_AI_API_ERRORS = (
    openai.error.APIConnectionError,
    openai.error.Timeout,
    openai.error.APIError,
    openai.error.ServiceUnavailableError,
)


def chat_gpt_moderated(input_text: str) -> bool:
    response = openai.Moderation.create(input=input_text)
    return response["results"][0]["flagged"]


def get_valid_messages_for_chat(chat: type[Chat], latest_query: str | None = None) -> list[dict]:
    """
    Get all messages for chat, append latest query if exists.
    Exclude invalid prompts (sensitive/moderated).
    """
    all_valid_chat_prompts = utils.get_all_valid_prompts_from_chat(chat)
    messages = []
    for prompt in all_valid_chat_prompts:
        user_prompt = {"role": "user", "content": prompt.user_prompt}
        messages.append(user_prompt)
        content = prompt.ai_response
        if content:
            ai_response = {"role": "assistant", "content": content}
            messages.append(ai_response)
    if latest_query:
        latest_prompt = {"role": "user", "content": latest_query}
        messages.append(latest_prompt)
    return messages


def get_text_from_gpt35_turbo_response(response: dict) -> str:
    content = response["choices"][0]["message"]["content"]
    return content


def get_gpt35_turbo_response(raw_inputs: dict) -> dict:
    response = openai.ChatCompletion.create(request_timeout=30, **raw_inputs)
    raw_ai_response = dict(response)
    response_content = get_text_from_gpt35_turbo_response(response)
    outputs_moderated = chat_gpt_moderated(response_content)
    tokens_input = raw_ai_response["usage"]["prompt_tokens"]
    tokens_output = raw_ai_response["usage"]["completion_tokens"]
    input_costs = tokens_input * constants.OPENAI_TOKEN_COSTS[raw_inputs["model"]]["INPUT_TOKEN_COST_DOLLARS"]
    output_costs = tokens_output * constants.OPENAI_TOKEN_COSTS[raw_inputs["model"]]["OUTPUT_TOKEN_COST_DOLLARS"]
    outputs = {
        "ai_response": response_content,
        "ai_response_moderated": outputs_moderated,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "cost_input_dollars": input_costs,
        "cost_output_dollars": output_costs,
    }
    return outputs


def num_tokens_from_string(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def is_prompt_over_token_limit(prompt_str: str, model: Prompt.LLMModels, buffer: int = 0) -> bool:
    model_name = model.label
    length = num_tokens_from_string(prompt_str, model_name)
    over_limit = length > (TOKEN_LIMITS[model] - buffer)
    return over_limit


def get_number_tokens_for_messages(messages: list[dict], model_name: str) -> int:
    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    if model_name not in (
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    ):
        raise NotImplementedError(f"Number of tokens is not implemented for model {model_name}.")
    tokens_per_message = 3
    tokens_per_name = 1
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def length_messages_over_token_limit(messages: list[dict], model: Prompt.LLMModels, buffer: int) -> tuple[int, bool]:
    # buffer - we don't want to hit the limit as then ChatGPT can't return anything
    token_limit = TOKEN_LIMITS[model]
    num_tokens = get_number_tokens_for_messages(messages, model.label)
    over_limit = num_tokens >= (token_limit - buffer)
    return num_tokens, over_limit


def get_latest_messages_to_token_limit(
    messages: list[dict], model: Prompt.LLMModels, buffer: int
) -> tuple[int, list[dict]]:
    output_messages = messages.copy()  # don't alter the original list
    num_tokens, over_limit = length_messages_over_token_limit(output_messages, model, buffer)
    while over_limit:
        output_messages.pop(0)
        num_tokens, over_limit = length_messages_over_token_limit(output_messages, model, buffer)
    return num_tokens, output_messages


def get_chat_gpt_inputs(chat: type[Chat], model: Prompt.LLMModels) -> dict:
    messages = get_valid_messages_for_chat(chat)
    num_tokens, truncated_messages = get_latest_messages_to_token_limit(messages, model=model, buffer=BUFFER_TOKENS)
    max_tokens = TOKEN_LIMITS[model] - num_tokens  # how many tokens can be in the response
    chat_gpt_inputs = {"model": model.label, "messages": truncated_messages, "max_tokens": max_tokens}
    return chat_gpt_inputs


def submit_valid_chat_to_chatgpt35(latest_prompt, chat_gpt_inputs):
    outputs = get_gpt35_turbo_response(chat_gpt_inputs)
    latest_prompt.ai_response = outputs.get("ai_response")
    latest_prompt.ai_response_moderated = outputs.get("ai_response_moderated")
    latest_prompt.tokens_input = outputs.get("tokens_input")
    latest_prompt.tokens_output = outputs.get("tokens_output")
    latest_prompt.cost_input_dollars = outputs.get("cost_input_dollars")
    latest_prompt.cost_output_dollars = outputs.get("cost_output_dollars")
    latest_prompt.save()
    return latest_prompt
