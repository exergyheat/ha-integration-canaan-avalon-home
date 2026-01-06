"""Support for Canaan Avalon Nano 3s LED light."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LED_EFFECT_ON, LED_EFFECT_OFF, MODELS_WITH_LED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canaan LED light from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    model_type = coordinator.model_type

    # Only add LED light for models that support it (Nano 3s)
    if model_type in MODELS_WITH_LED:
        async_add_entities([CanaanLEDLight(coordinator)])


class CanaanLEDLight(CoordinatorEntity, LightEntity):
    """Representation of Canaan Avalon Nano 3s LED light."""

    _attr_icon = "mdi:led-strip-variant"
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(self, coordinator) -> None:
        """Initialize the LED light."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_led"
        self._attr_name = "LED"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            name=self.coordinator.name,
            manufacturer=self.coordinator.data.get("make", "Canaan"),
            model=self.coordinator.data.get("model", "Avalon Nano 3s"),
            configuration_url=f"http://{self.coordinator.data['ip']}",
        )

    @property
    def is_on(self) -> bool:
        """Return true if LED is on."""
        return self.coordinator.data.get("led_on", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the LED (0-255)."""
        # Nano 3s uses 0-100 scale, convert to 0-255
        led_brightness = self.coordinator.data.get("led_brightness", 0)
        return int(led_brightness * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color of the LED."""
        r = self.coordinator.data.get("led_r", 255)
        g = self.coordinator.data.get("led_g", 255)
        b = self.coordinator.data.get("led_b", 255)
        return (r, g, b)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the LED."""
        # Get current settings as defaults
        effect = self.coordinator.data.get("led_effect", LED_EFFECT_ON)
        if effect == LED_EFFECT_OFF:
            effect = LED_EFFECT_ON  # Turn on with "On" effect if currently off
        
        brightness = self.coordinator.data.get("led_brightness", 100)
        color_temp = self.coordinator.data.get("led_color_temp", 100)
        r = self.coordinator.data.get("led_r", 255)
        g = self.coordinator.data.get("led_g", 255)
        b = self.coordinator.data.get("led_b", 255)

        # Handle brightness from HA (0-255 scale)
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)

        # Handle RGB color
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]

        try:
            _LOGGER.info(f"Turning on LED on {self.coordinator.miner_ip}: brightness={brightness}, rgb=({r},{g},{b})")
            success = await self.coordinator.api.set_led(
                effect=effect,
                brightness=brightness,
                color_temp=color_temp,
                r=r,
                g=g,
                b=b,
            )
            if success:
                _LOGGER.info(f"LED turned on on {self.coordinator.miner_ip}")
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to turn on LED on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to turn on LED on {self.coordinator.miner_ip}: {err}")
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the LED."""
        # Preserve other settings but set effect to Off
        brightness = self.coordinator.data.get("led_brightness", 100)
        color_temp = self.coordinator.data.get("led_color_temp", 100)
        r = self.coordinator.data.get("led_r", 255)
        g = self.coordinator.data.get("led_g", 255)
        b = self.coordinator.data.get("led_b", 255)

        try:
            _LOGGER.info(f"Turning off LED on {self.coordinator.miner_ip}")
            success = await self.coordinator.api.set_led(
                effect=LED_EFFECT_OFF,
                brightness=brightness,
                color_temp=color_temp,
                r=r,
                g=g,
                b=b,
            )
            if success:
                _LOGGER.info(f"LED turned off on {self.coordinator.miner_ip}")
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to turn off LED on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to turn off LED on {self.coordinator.miner_ip}: {err}")
            raise
