"""Fixtures for OpenCode integration tests."""

from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator
from typing import Any, Literal
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.opencode.const import DOMAIN
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LLM_HASS_API,
    CONF_MODEL,
    CONF_PROMPT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.setup import async_setup_component
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from tests.common import MockConfigEntry


def _make_chunk(
    content: str | None = None,
    *,
    role: Literal["assistant"] | None = None,
    tool_calls: list[Any] | None = None,
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


async def _stream(*chunks: ChatCompletionChunk) -> AsyncIterator[ChatCompletionChunk]:
    """Yield chat completion chunks as an asynchronous stream."""
    for chunk in chunks:
        yield chunk


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.opencode.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def enable_assist() -> bool:
    """Mock conversation subentry data."""
    return False


@pytest.fixture
def conversation_subentry_data(enable_assist: bool) -> dict[str, Any]:
    """Mock conversation subentry data."""
    res: dict[str, Any] = {
        CONF_MODEL: "deepseek-v4-flash",
        CONF_PROMPT: "You are a helpful assistant.",
    }
    if enable_assist:
        res[CONF_LLM_HASS_API] = [llm.LLM_API_ASSIST]
    return res


@pytest.fixture
def ai_task_data_subentry_data() -> dict[str, Any]:
    """Mock AI task subentry data."""
    return {
        CONF_MODEL: "deepseek-v4-flash",
    }


@pytest.fixture
def mock_config_entry(
    hass: HomeAssistant,
    conversation_subentry_data: dict[str, Any],
    ai_task_data_subentry_data: dict[str, Any],
) -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        title="OpenCode Zen",
        domain=DOMAIN,
        data={
            CONF_API_KEY: "bla",
        },
        version=1,
        subentries_data=[
            ConfigSubentryData(
                data=conversation_subentry_data,
                subentry_id="ABCDEF",
                subentry_type="conversation",
                title="deepseek-v4-flash",
                unique_id=None,
            ),
            ConfigSubentryData(
                data=ai_task_data_subentry_data,
                subentry_id="ABCDEG",
                subentry_type="ai_task_data",
                title="deepseek-v4-flash",
                unique_id=None,
            ),
        ],
    )


@pytest.fixture
def openai_compatible_model_ids() -> list[str]:
    """Mock model IDs (OpenAI-compatible only, as filtered by the integration)."""
    return [
        "deepseek-v4-flash",
        "deepseek-v4-flash-free",
        "glm-5",
        "kimi-k2.5",
        "minimax-m3",
    ]


@pytest.fixture
def mock_stream() -> Callable[..., AsyncIterator[ChatCompletionChunk]]:
    """Return a factory for asynchronous chat completion streams."""

    def _make_stream(
        *chunks: ChatCompletionChunk,
    ) -> AsyncIterator[ChatCompletionChunk]:
        return _stream(*chunks)

    return _make_stream


@pytest.fixture
async def mock_openai_client() -> AsyncGenerator[AsyncMock]:
    """Initialize integration with a mocked OpenAI client."""
    with patch("custom_components.opencode.AsyncOpenAI") as mock_client:
        client = mock_client.return_value
        client.chat.completions.create = AsyncMock(
            return_value=_stream(
                _make_chunk(role="assistant", content="Hello, how can I help you?"),
                _make_chunk(finish_reason="stop"),
            )
        )
        yield client


@pytest.fixture(autouse=True)
async def setup_ha(hass: HomeAssistant) -> None:
    """Set up Home Assistant."""
    assert await async_setup_component(hass, "homeassistant", {})
