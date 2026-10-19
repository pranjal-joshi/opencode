"""Tests for the OpenCode conversation agent."""

from collections.abc import AsyncIterator, Callable
from typing import Literal
from unittest.mock import AsyncMock

import openai
import pytest
from homeassistant.components import conversation
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import intent
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import (
    ChoiceDelta,
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)

from tests.common import MockConfigEntry
from tests.components.conversation import MockChatLog, mock_chat_log  # noqa: F401


def _chunk(
    content: str | None = None,
    *,
    role: Literal["assistant"] | None = None,
    tool_calls: list[ChoiceDeltaToolCall] | None = None,
    finish_reason: str | None = None,
) -> ChatCompletionChunk:
    """Build a streaming chat completion chunk."""
    return ChatCompletionChunk(
        id="chatcmpl-1234567890ABCDEFGHIJKLMNOPQRS",
        choices=[
            ChunkChoice(
                index=0,
                delta=ChoiceDelta(role=role, content=content, tool_calls=tool_calls),
                finish_reason=finish_reason,
            )
        ],
        created=1700000000,
        model="deepseek-v4-flash",
        object="chat.completion.chunk",
    )


def _assistant_completion(content: str) -> ChatCompletion:
    """Build a non-streaming chat completion for the fallback path."""
    return ChatCompletion(
        id="chatcmpl-1234567890ABCDEFGHIJKLMNOPQRS",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content=content,
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
        usage=CompletionUsage(completion_tokens=9, prompt_tokens=8, total_tokens=17),
    )


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

    assert hass.states.get("conversation.deepseek_v4_flash").state == "unavailable"
    assert entity_registry.async_get("conversation.deepseek_v4_flash")


async def test_default_prompt(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Test that the default prompt works and the response is streamed."""
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
    assert mock_chat_log.content[-1].content == "Hello, how can I help you?"
    call = mock_openai_client.chat.completions.create.call_args_list[0][1]
    assert call["model"] == "deepseek-v4-flash"
    assert call["user"] == mock_chat_log.conversation_id
    assert call["stream"] is True


async def test_empty_api_response(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
    mock_stream: Callable[..., AsyncIterator[ChatCompletionChunk]],
) -> None:
    """Test that an empty stream raises HomeAssistantError."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_stream())

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_streaming_fallback_to_non_streaming(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Test that streaming falls back to a non-streaming request on error."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_openai_client.chat.completions.create.side_effect = [
        openai.OpenAIError("streaming is not supported"),
        _assistant_completion("Fallback response"),
    ]

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_chat_log.content[-1].content == "Fallback response"
    assert mock_openai_client.chat.completions.create.call_count == 2
    assert (
        mock_openai_client.chat.completions.create.call_args_list[0][1]["stream"]
        is True
    )
    assert (
        "stream" not in mock_openai_client.chat.completions.create.call_args_list[1][1]
    )


@pytest.mark.parametrize("enable_assist", [True])
async def test_function_call(
    hass: HomeAssistant,
    mock_chat_log: MockChatLog,  # noqa: F811
    mock_config_entry: MockConfigEntry,
    mock_openai_client: AsyncMock,
    mock_stream: Callable[..., AsyncIterator[ChatCompletionChunk]],
) -> None:
    """Test a streamed tool call with fragmented arguments is reassembled."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_chat_log.mock_tool_results({"call_call_1": "value1"})

    mock_openai_client.chat.completions.create.side_effect = [
        mock_stream(
            _chunk(
                role="assistant",
                tool_calls=[
                    ChoiceDeltaToolCall(
                        index=0,
                        id="call_call_1",
                        type="function",
                        function=ChoiceDeltaToolCallFunction(
                            name="test_tool", arguments='{"para'
                        ),
                    )
                ],
            ),
            _chunk(
                tool_calls=[
                    ChoiceDeltaToolCall(
                        index=0,
                        function=ChoiceDeltaToolCallFunction(arguments='m1":"call1"}'),
                    )
                ],
            ),
            _chunk(finish_reason="tool_calls"),
        ),
        mock_stream(
            _chunk(role="assistant", content="Done"),
            _chunk(finish_reason="stop"),
        ),
    ]

    result = await conversation.async_converse(
        hass,
        "hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.deepseek_v4_flash",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_openai_client.chat.completions.create.call_count == 2

    assistant_with_tools = next(
        content
        for content in mock_chat_log.content
        if isinstance(content, conversation.AssistantContent) and content.tool_calls
    )
    assert assistant_with_tools.tool_calls[0].tool_name == "test_tool"
    assert assistant_with_tools.tool_calls[0].tool_args == {"param1": "call1"}
    assert any(
        isinstance(content, conversation.ToolResultContent)
        for content in mock_chat_log.content
    )
