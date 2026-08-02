"""Tests for the OpenCode conversation agent."""

from unittest.mock import AsyncMock

from homeassistant.components import conversation
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import intent
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from tests.common import MockConfigEntry
from tests.components.conversation import MockChatLog, mock_chat_log  # noqa: F401


async def test_all_entities(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that the conversation entity is registered."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        hass.states.get("conversation.deepseek_v4_flash").state
        == "unavailable"
    )
    assert entity_registry.async_get("conversation.deepseek_v4_flash")


async def test_default_prompt(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Test that the default prompt works."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    call = mock_openai_client.chat.completions.create.call_args_list[0][1]
    assert call["model"] == "deepseek-v4-flash"
    assert call["user"] == mock_chat_log.conversation_id


async def test_empty_api_response(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Test that an empty choices response raises HomeAssistantError."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=ChatCompletion(
            id="chatcmpl-1234567890ABCDEFGHIJKLMNOPQRS",
            choices=[],
            created=1700000000,
            model="deepseek-v4-flash",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(completion_tokens=0, prompt_tokens=8, total_tokens=8),
        )
    )

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_function_call(
    hass: HomeAssistant,
    mock_chat_log: MockChatLog,  # noqa: F811
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
) -> None:
    """Test function call from the assistant."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_openai_client.chat.completions.create.side_effect = (
        ChatCompletion(
            id="chatcmpl-1234567890ABCDEFGHIJKLMNOPQRS",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    message=ChatCompletionMessage(
                        content=None,
                        role="assistant",
                        function_call=None,
                        tool_calls=None,
                    ),
                )
            ],
            created=1700000000,
            model="deepseek-v4-flash",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(
                completion_tokens=9, prompt_tokens=8, total_tokens=17
            ),
        ),
        ChatCompletion(
            id="chatcmpl-1234567890ZYXWVUTSRQPONMLKJIH",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(
                        content="I have successfully called the function",
                        role="assistant",
                        function_call=None,
                        tool_calls=None,
                    ),
                )
            ],
            created=1700000000,
            model="deepseek-v4-flash",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(
                completion_tokens=9, prompt_tokens=8, total_tokens=17
            ),
        ),
    )

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_openai_client.chat.completions.create.call_count == 2
