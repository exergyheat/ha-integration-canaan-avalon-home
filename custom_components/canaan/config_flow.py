"""Config flow for Canaan Avalon Miner integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_IP,
    CONF_MODEL,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODEL_NAMES,
    MODEL_UNKNOWN,
)
from .coordinator import CanaanAPI, detect_model

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect and detect model.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_IP]
    port = data.get(CONF_PORT, DEFAULT_PORT)
    
    # Detect model type
    model_type, model_name = await detect_model(host, port)
    
    if model_type == MODEL_UNKNOWN:
        # Try to connect anyway to verify connectivity
        api = CanaanAPI(host=host, port=port)
        response = await api.get_version()
        if not response:
            # Try estats as fallback
            response = await api.get_stats()
        if not response:
            raise CannotConnect
    
    _LOGGER.info(f"Detected {model_name} at {host}")

    # Return info that you want to store in the config entry.
    return {
        "title": data.get(CONF_NAME, f"{model_name} {host}"),
        "ip": host,
        "model_type": model_type,
        "model_name": model_name,
    }


class CanaanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Canaan Avalon Miner."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_ip: str | None = None
        self._model_type: str | None = None
        self._model_name: str | None = None
        self._errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - ask for IP address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate IP can connect to miner and detect model
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_IP])
                self._abort_if_unique_id_configured()
                
                # Store discovered info for next step
                self._discovered_ip = user_input[CONF_IP]
                self._model_type = info["model_type"]
                self._model_name = info["model_name"]
                
                # Move to name step
                return await self.async_step_name()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_name(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the name and options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Create the config entry with model info
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_IP: self._discovered_ip,
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_MODEL: self._model_type,
                    "model_name": self._model_name,
                },
            )

        # Show form with name and options - use IP as default (don't include model in device name)
        default_name = self._discovered_ip
        
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=default_name): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            }
        )

        return self.async_show_form(
            step_id="name",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "ip": self._discovered_ip,
                "model": self._model_name or "Unknown",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CanaanOptionsFlowHandler:
        """Get the options flow for this handler."""
        return CanaanOptionsFlowHandler(config_entry)


class CanaanOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Canaan integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PORT,
                        default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): cv.port,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
