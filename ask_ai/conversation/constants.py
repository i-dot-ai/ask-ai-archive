from ask_ai.conversation.models import Prompt

# https://openai.com/pricing
# Costs given in dollars per one thousand tokens
OPENAI_TOKEN_COSTS = {
    # GPT 3.5 Turbo model, 4K context - gpt-3.5-turbo-0613
    Prompt.LLMModels.GPT35_TURBO.label: {  # type: ignore
        "INPUT_TOKEN_COST_DOLLARS": 0.0015 / 1000,
        "OUTPUT_TOKEN_COST_DOLLARS": 0.002 / 1000,
    },
    # GPT 3.5 Turbo model, 16K context - gpt-3.5-turbo-1106
    Prompt.LLMModels.GPT35_TURBO_1106.label: {  # type: ignore
        "INPUT_TOKEN_COST_DOLLARS": 0.0010 / 1000,
        "OUTPUT_TOKEN_COST_DOLLARS": 0.002 / 1000,
    },
    # GPT 3.5 Turbo model, 16k context - gpt-3,5-turbo-0125
    Prompt.LLMModels.GPT35_TURBO_0125.label: {  # type: ignore
        "INPUT_TOKEN_COST_DOLLARS": 0.0005 / 1000,
        "OUTPUT_TOKEN_COST_DOLLARS": 0.0015 / 1000,
    },
}

TOKEN_LIMITS = {
    Prompt.LLMModels.GPT35_TURBO: 4096,
    Prompt.LLMModels.GPT35_TURBO_1106: 4096,  # 1106 model has a 16k context window, but still only a 4k token limit
    Prompt.LLMModels.GPT35_TURBO_0125: 4096,  # 0125 model has a 16k context window, but still only a 4k token limit
}
BUFFER_TOKENS = 200  # Buffer is so that there are enough tokens for ChatGPT to respond
