import pytest

from ask_ai.conversation import chat_gpt, constants, models


def mock_chat_gpt_moderation_true(input):
    response = {
        "id": "modr-XXXXX",
        "model": "text-moderation-005",
        "results": [
            {
                "flagged": True,
                "categories": {
                    "sexual": False,
                    "hate": False,
                    "harassment": False,
                    "self-harm": False,
                    "sexual/minors": False,
                    "hate/threatening": False,
                    "violence/graphic": False,
                    "self-harm/intent": False,
                    "self-harm/instructions": False,
                    "harassment/threatening": True,
                    "violence": True,
                },
                "category_scores": {
                    "sexual": 1.2282071e-06,
                    "hate": 0.010696256,
                    "harassment": 0.29842457,
                    "self-harm": 1.5236925e-08,
                    "sexual/minors": 5.7246268e-08,
                    "hate/threatening": 0.0060676364,
                    "violence/graphic": 4.435014e-06,
                    "self-harm/intent": 8.098441e-10,
                    "self-harm/instructions": 2.8498655e-11,
                    "harassment/threatening": 0.63055265,
                    "violence": 0.99011886,
                },
            }
        ],
    }
    return response


def mock_chat_gpt_moderation_false(input):
    response = {
        "id": "modr-XXXXX",
        "model": "text-moderation-005",
        "results": [{"flagged": False}],
    }
    return response


def mock_chat_completion_gpt35_response(**inputs):
    output = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "This is some new content from ChatGPT.",
                    "role": "assistant",
                },
            }
        ],
        "created": 1677664795,
        "id": "7QyqpwdfhqwajicIEznoc6Q47XAyW",
        "model": "gpt-3.5-turbo-0613",
        "object": "chat.completion",
        "usage": {"completion_tokens": 17, "prompt_tokens": 57, "total_tokens": 74},
    }
    return output


def mock_get_gpt35_turbo_response(raw_inputs):
    outputs = {
        "ai_response": "Mocked response",
        "ai_response_moderated": True,
        "tokens_input": 57,
        "tokens_output": 17,
        "cost_input_dollars": 0.05,
        "cost_output_dollars": 0.9,
    }
    return outputs


def test_chat_gpt_moderated(monkeypatch):
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_true)
    output = chat_gpt.chat_gpt_moderated("test input")
    assert output, output
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    output = chat_gpt.chat_gpt_moderated("test input")
    assert not output, output


@pytest.mark.django_db
def test_get_valid_messages_for_chat(peter_chat):
    expected_messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
        {"role": "user", "content": "latest prompt"},
    ]
    actual = chat_gpt.get_valid_messages_for_chat(peter_chat, latest_query="latest prompt")
    assert actual == expected_messages, actual


@pytest.mark.django_db
def test_get_chat_gpt_inputs(peter_chat):
    expected_messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
    ]
    token_limit = constants.TOKEN_LIMITS[models.Prompt.LLMModels.GPT35_TURBO_0125]
    expected = {"model": "gpt-3.5-turbo-0125", "messages": expected_messages, "max_tokens": (token_limit - 39)}
    actual = chat_gpt.get_chat_gpt_inputs(peter_chat, models.Prompt.LLMModels.GPT35_TURBO_0125)
    assert expected == actual, actual


def test_get_text_from_gpt35_turbo_response(monkeypatch):
    messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
        {"role": "user", "content": "latest prompt"},
    ]
    inputs = {"model": models.Prompt.LLMModels.GPT35_TURBO_0125.label, "messages": messages}
    monkeypatch.setattr("openai.ChatCompletion.create", mock_chat_completion_gpt35_response)
    monkeypatch.setattr("openai.Moderation.create", mock_chat_gpt_moderation_false)
    outputs = chat_gpt.get_gpt35_turbo_response(inputs)
    assert outputs["ai_response"] == "This is some new content from ChatGPT.", outputs["ai_response"]
    assert not outputs["ai_response_moderated"], outputs["ai_response_moderated"]
    assert outputs["tokens_input"] == 57
    assert outputs["tokens_output"] == 17
    assert outputs["cost_input_dollars"] == (
        57 * constants.OPENAI_TOKEN_COSTS[models.Prompt.LLMModels.GPT35_TURBO_0125.label]["INPUT_TOKEN_COST_DOLLARS"]
    ), outputs["cost_input_dollars"]
    assert outputs["cost_output_dollars"] == (
        17 * constants.OPENAI_TOKEN_COSTS[models.Prompt.LLMModels.GPT35_TURBO_0125.label]["OUTPUT_TOKEN_COST_DOLLARS"]
    ), outputs["cost_output_dollars"]


def test_num_tokens_from_string():
    example_string = "How many tokens is this for GPT3.5 turbo?"
    tokens = chat_gpt.num_tokens_from_string(example_string, "gpt-3.5-turbo")
    assert tokens == 13, tokens


def test_is_prompt_over_token_limit():
    assert not chat_gpt.is_prompt_over_token_limit("tiny prompt", models.Prompt.LLMModels.GPT35_TURBO_0125)
    assert chat_gpt.is_prompt_over_token_limit("MASSIVE prompt" * 4000, models.Prompt.LLMModels.GPT35_TURBO_0125)


def test_get_number_tokens_for_messages():
    messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
        {"role": "user", "content": "Do they eat fish in Spain?"},
    ]
    num_tokens = chat_gpt.get_number_tokens_for_messages(messages, models.Prompt.LLMModels.GPT35_TURBO_0125.label)
    expected_num_tokens = 50  # Checked against ChatGPT response
    assert num_tokens == expected_num_tokens, num_tokens


def test_length_messages_over_token_limit():
    short_messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
        {"role": "user", "content": "Do they eat fish in Spain?"},
    ]
    over_the_limit_messages = [
        {"role": "user", "content": "What is the capital of Spain?" * 500},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked" * 500},
        {"role": "assistant", "content": "Some response" * 100},
        {"role": "user", "content": "Do they eat fish in Spain?"},
    ]
    small_buffer = 10
    massive_buffer = 4050
    num_tokens, over_limit = chat_gpt.length_messages_over_token_limit(
        short_messages, models.Prompt.LLMModels.GPT35_TURBO_1106, buffer=small_buffer
    )
    assert not over_limit, num_tokens
    num_tokens, over_limit = chat_gpt.length_messages_over_token_limit(
        short_messages, models.Prompt.LLMModels.GPT35_TURBO_1106, buffer=massive_buffer
    )
    assert over_limit, num_tokens
    num_tokens, over_limit = chat_gpt.length_messages_over_token_limit(
        over_the_limit_messages, models.Prompt.LLMModels.GPT35_TURBO_1106, buffer=small_buffer
    )
    assert over_limit, num_tokens


def test_get_latest_messages_to_token_limit():
    messages = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "Flagged sensitive prompt, shouldn't be blocked"},
        {"role": "assistant", "content": "Some response"},
        {"role": "user", "content": "Do they eat fish in Spain?"},
    ]
    original_token_length = chat_gpt.get_number_tokens_for_messages(
        messages, models.Prompt.LLMModels.GPT35_TURBO_1106.label
    )
    num_tokens, output_messages = chat_gpt.get_latest_messages_to_token_limit(
        messages, models.Prompt.LLMModels.GPT35_TURBO_1106, buffer=10
    )
    assert len(output_messages) == 5, output_messages  # should be the same messages
    assert original_token_length == num_tokens, output_messages
    messages = [
        {"role": "user", "content": "What are elephants?"},
        {"role": "assistant", "content": "What are elephants?"},
        {"role": "user", "content": "A troupe of jugglers and acrobats" * 100},
        {"role": "assistant", "content": "A really long response" * 3000},
        {"role": "user", "content": "the aroma of apple pies wafts from the nearby bakery"},
        {"role": "assistant", "content": "Medium-sized fake AI response" * 100},
        {"role": "user", "content": "fishes and octopuses"},
    ]
    num_tokens, output_messages = chat_gpt.get_latest_messages_to_token_limit(
        messages, models.Prompt.LLMModels.GPT35_TURBO, buffer=10
    )
    assert len(output_messages) < 7, output_messages
    assert num_tokens <= (constants.TOKEN_LIMITS[models.Prompt.LLMModels.GPT35_TURBO_1106] - 10), output_messages


@pytest.mark.django_db
def test_submit_valid_chat_to_chatgpt35(monkeypatch, peter_chat, peter_rabbit_prompt):
    inputs = chat_gpt.get_chat_gpt_inputs(chat=peter_chat, model=models.Prompt.LLMModels.GPT35_TURBO_1106)
    monkeypatch.setattr("ask_ai.conversation.chat_gpt.get_gpt35_turbo_response", mock_get_gpt35_turbo_response)
    latest_prompt = chat_gpt.submit_valid_chat_to_chatgpt35(latest_prompt=peter_rabbit_prompt, chat_gpt_inputs=inputs)
    assert latest_prompt.ai_response == "Mocked response"
    assert latest_prompt.ai_response_moderated
    assert latest_prompt.tokens_input == 57
    assert latest_prompt.tokens_output == 17
    assert latest_prompt.cost_input_dollars == 0.05
    assert latest_prompt.cost_output_dollars == 0.9
