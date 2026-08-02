"""Constants for the OpenCode integration."""

import logging

from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT
from homeassistant.helpers import llm

DOMAIN = "opencode"
LOGGER = logging.getLogger(__package__)

CONF_BASE_URL = "base_url"
CONF_RECOMMENDED = "recommended"

DEFAULT_BASE_URL = "https://opencode.ai/zen/v1"

# Model families on OpenCode Zen that are NOT served through the OpenAI
# Chat Completions endpoint (`/chat/completions`). We filter these out of the
# model picker because v1 only speaks the OpenAI-compatible protocol.
EXCLUDED_MODEL_PREFIXES = ("gpt-", "grok-", "claude-", "qwen", "gemini-")

RECOMMENDED_CONVERSATION_OPTIONS = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
}


def is_openai_compatible_model(model_id: str) -> bool:
    """Return True if the model is served through the OpenAI-compatible endpoint.

    OpenCode Zen splits its catalog across several protocols (Responses,
    Anthropic Messages, Google, and OpenAI Chat Completions). The models
    endpoint does not expose protocol metadata, so we filter by prefix.
    """
    return not model_id.startswith(EXCLUDED_MODEL_PREFIXES)
