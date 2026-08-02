"""Test the OpenCode config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.opencode.config_flow import CannotConnect, InvalidAuth
from homeassistant.components.opencode.const import (
    CONF_PROMPT,
    DEFAULT_BASE_URL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_setup_entry")
async def test_full_flow(
    hass: HomeAssistant,
    openai_compatible_model_ids: list[str],
) -> None:
    """Test the full config flow."""
    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=openai_compatible_model_ids,
    ) as mock_get_models:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "bla"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OpenCode Zen"
    assert result["data"] == {
        CONF_API_KEY: "bla",
        "base_url": DEFAULT_BASE_URL,
    }
    mock_get_models.assert_awaited_once_with(hass, DEFAULT_BASE_URL, "bla")


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (InvalidAuth("invalid auth"), "invalid_auth"),
        (CannotConnect("cannot connect"), "cannot_connect"),
        (Exception, "unknown"),
    ],
)
@pytest.mark.usefixtures("mock_setup_entry")
async def test_form_errors(
    hass: HomeAssistant,
    exception: Exception,
    error: str,
) -> None:
    """Test we handle errors from the OpenCode API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "custom_components.opencode.config_flow._get_models",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "bla"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


@pytest.mark.usefixtures("mock_setup_entry")
async def test_duplicate_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    openai_compatible_model_ids: list[str],
) -> None:
    """Test aborting the flow if an entry already exists."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]
    assert result["step_id"] == "user"

    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=openai_compatible_model_ids,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "bla"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_create_conversation_agent(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    openai_compatible_model_ids: list[str],
) -> None:
    """Test creating a conversation agent."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=openai_compatible_model_ids,
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]
        assert result["step_id"] == "init"

        assert result["data_schema"].schema["model"].config["options"] == [
            {"value": model, "label": model}
            for model in openai_compatible_model_ids
        ]

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_MODEL: "deepseek-v4-flash",
                CONF_PROMPT: "you are an assistant",
                CONF_LLM_HASS_API: ["assist"],
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_MODEL: "deepseek-v4-flash",
        CONF_PROMPT: "you are an assistant",
        CONF_LLM_HASS_API: ["assist"],
    }


async def test_create_conversation_agent_no_control(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    openai_compatible_model_ids: list[str],
) -> None:
    """Test creating a conversation agent without control over the LLM API."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=openai_compatible_model_ids,
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]
        assert result["step_id"] == "init"

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_MODEL: "deepseek-v4-flash",
                CONF_PROMPT: "you are an assistant",
                CONF_LLM_HASS_API: [],
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_MODEL: "deepseek-v4-flash",
        CONF_PROMPT: "you are an assistant",
    }


async def test_subentry_filters_non_compatible_models(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that non-OpenAI-compatible models are filtered out."""
    all_models = [
        "claude-sonnet-5",
        "deepseek-v4-flash",
        "gemini-3.5-flash",
        "gpt-5",
        "grok-4.5",
        "kimi-k2.5",
        "qwen3.7-plus",
    ]
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=all_models,
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["data_schema"].schema["model"].config["options"] == [
        {"value": "deepseek-v4-flash", "label": "deepseek-v4-flash"},
        {"value": "kimi-k2.5", "label": "kimi-k2.5"},
    ]


@pytest.mark.parametrize(
    ("exception", "reason"),
    [
        (InvalidAuth("invalid auth"), "invalid_auth"),
        (CannotConnect("cannot connect"), "cannot_connect"),
        (Exception, "unknown"),
    ],
)
async def test_subentry_exceptions(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    reason: str,
) -> None:
    """Test subentry flow exceptions."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.opencode.config_flow._get_models",
        side_effect=exception,
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == reason


async def test_reconfigure_conversation_agent(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    openai_compatible_model_ids: list[str],
) -> None:
    """Test reconfiguring a conversation agent."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    subentry_id = "ABCDEF"

    with patch(
        "custom_components.opencode.config_flow._get_models",
        return_value=openai_compatible_model_ids,
    ):
        result = await mock_config_entry.start_subentry_reconfigure_flow(
            hass, subentry_id
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_MODEL: "kimi-k2.5",
                CONF_PROMPT: "updated prompt",
                CONF_LLM_HASS_API: ["assist"],
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    subentry = mock_config_entry.subentries[subentry_id]
    assert subentry.data[CONF_MODEL] == "kimi-k2.5"
    assert subentry.data[CONF_PROMPT] == "updated prompt"
    assert subentry.data[CONF_LLM_HASS_API] == ["assist"]


async def test_reconfigure_entry_not_loaded(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguring when the entry is not loaded."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"
