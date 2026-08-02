"""The OpenCode integration."""

from openai import AsyncOpenAI, AuthenticationError, OpenAIError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.httpx_client import get_async_client

from .const import CONF_BASE_URL, DEFAULT_BASE_URL, LOGGER

PLATFORMS = [Platform.CONVERSATION]

type OpenCodeConfigEntry = ConfigEntry[AsyncOpenAI]


def _create_client(hass: HomeAssistant, entry: OpenCodeConfigEntry) -> AsyncOpenAI:
    """Create an AsyncOpenAI client for the OpenCode Zen endpoint."""
    return AsyncOpenAI(
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        api_key=entry.data[CONF_API_KEY],
        http_client=get_async_client(hass),
    )


async def async_setup_entry(hass: HomeAssistant, entry: OpenCodeConfigEntry) -> bool:
    """Set up OpenCode from a config entry."""
    client = _create_client(hass, entry)

    try:
        async for _ in client.with_options(timeout=10.0).models.list():
            break
    except AuthenticationError as err:
        LOGGER.error("Invalid API key: %s", err)
        raise ConfigEntryError("Invalid API key") from err
    except OpenAIError as err:
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: OpenCodeConfigEntry
) -> None:
    """Handle update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: OpenCodeConfigEntry) -> bool:
    """Unload OpenCode."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
