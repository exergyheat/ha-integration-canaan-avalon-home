"""Support for Canaan Avalon Miner select entities."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    LED_EFFECTS,
    MODEL_NANO3,
    MODEL_NANO3S,
    MODEL_Q,
    MODELS_WITH_LED,
    MODELS_WITH_NANO3_LEVELS,
    MODELS_WITH_Q_LEVELS,
    MODELS_WITH_WORK_LEVEL,
    MODELS_WITH_WORK_MODE,
    WORK_LEVELS_MINI3,
    WORK_LEVELS_Q,
    WORK_MODES_MINI3,
    WORK_MODES_NANO3S,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canaan select entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    model_type = coordinator.model_type

    entities = []
    
    # Add work mode selector for models that support it
    # Mini 3: heating/mining/night; Nano 3 and Nano 3s: low/mid/high
    if model_type in MODELS_WITH_WORK_MODE or model_type in MODELS_WITH_NANO3_LEVELS:
        entities.append(CanaanWorkModeSelect(coordinator))
    
    # Add work level selector for Mini 3 (Super/Eco)
    if model_type in MODELS_WITH_WORK_LEVEL:
        entities.append(CanaanWorkLevelSelect(coordinator))
    
    # Add work level selector for Avalon Q (Eco/Standard/Super)
    if model_type in MODELS_WITH_Q_LEVELS:
        entities.append(CanaanQLevelSelect(coordinator))
    
    # Add LED effect selector for Nano 3s
    if model_type in MODELS_WITH_LED:
        entities.append(CanaanLEDEffectSelect(coordinator))

    async_add_entities(entities)


class CanaanWorkModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of Canaan Avalon Miner work mode selector."""

    _attr_icon = "mdi:wrench"

    def __init__(self, coordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_work_mode"
        self._attr_name = "Work Mode"
        self._attr_has_entity_name = True
        
        # Set options based on model type
        self._model_type = coordinator.model_type
        if self._model_type in (MODEL_NANO3, MODEL_NANO3S):
            self._work_modes = WORK_MODES_NANO3S
        else:
            self._work_modes = WORK_MODES_MINI3
        self._attr_options = list(self._work_modes.keys())

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            name=self.coordinator.name,
            manufacturer=self.coordinator.data.get("make", "Canaan"),
            model=self.coordinator.data.get("model", "Avalon Miner"),
            configuration_url=f"http://{self.coordinator.data['ip']}",
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected mode."""
        return self.coordinator.data.get("mode", "Unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self._work_modes:
            _LOGGER.error(f"Invalid work mode: {option}")
            return

        mode_value = self._work_modes[option]
        
        try:
            _LOGGER.info(f"Setting work mode to {option} ({mode_value}) on {self.coordinator.miner_ip}")
            success = await self.coordinator.api.set_work_mode(mode_value)
            if success:
                _LOGGER.info(f"Work mode set to {option} on {self.coordinator.miner_ip}")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to set work mode on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to set work mode on {self.coordinator.miner_ip}: {err}")
            raise


class CanaanWorkLevelSelect(CoordinatorEntity, SelectEntity):
    """Representation of Canaan Avalon Mini 3 work level selector (Super/Eco)."""

    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_work_level"
        self._attr_name = "Work Level"
        self._attr_options = list(WORK_LEVELS_MINI3.keys())
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            name=self.coordinator.name,
            manufacturer=self.coordinator.data.get("make", "Canaan"),
            model=self.coordinator.data.get("model", "Avalon Miner"),
            configuration_url=f"http://{self.coordinator.data['ip']}",
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected level."""
        return self.coordinator.data.get("level", "Unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in WORK_LEVELS_MINI3:
            _LOGGER.error(f"Invalid work level: {option}")
            return

        level_value = WORK_LEVELS_MINI3[option]
        
        try:
            _LOGGER.info(f"Setting work level to {option} ({level_value}) on {self.coordinator.miner_ip}")
            success = await self.coordinator.api.set_work_level(level_value)
            if success:
                _LOGGER.info(f"Work level set to {option} on {self.coordinator.miner_ip}")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to set work level on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to set work level on {self.coordinator.miner_ip}: {err}")
            raise


class CanaanQLevelSelect(CoordinatorEntity, SelectEntity):
    """Representation of Avalon Q performance level selector (Eco/Standard/Super)."""

    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_work_level"
        self._attr_name = "Work Level"
        self._attr_options = list(WORK_LEVELS_Q.keys())
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            name=self.coordinator.name,
            manufacturer=self.coordinator.data.get("make", "Canaan"),
            model=self.coordinator.data.get("model", "Avalon Q"),
            configuration_url=f"http://{self.coordinator.data['ip']}",
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected level."""
        return self.coordinator.data.get("level", "Unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in WORK_LEVELS_Q:
            _LOGGER.error(f"Invalid work level: {option}")
            return

        level_value = WORK_LEVELS_Q[option]
        
        try:
            _LOGGER.info(f"Setting work level to {option} ({level_value}) on {self.coordinator.miner_ip}")
            # For Q, use set_work_mode since it uses WORKMODE field for levels
            success = await self.coordinator.api.set_work_mode(level_value)
            if success:
                _LOGGER.info(f"Work level set to {option} on {self.coordinator.miner_ip}")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to set work level on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to set work level on {self.coordinator.miner_ip}: {err}")
            raise


class CanaanLEDEffectSelect(CoordinatorEntity, SelectEntity):
    """Representation of Canaan Avalon Nano 3s LED effect selector."""

    _attr_icon = "mdi:led-on"

    def __init__(self, coordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_led_effect"
        self._attr_name = "LED Effect"
        self._attr_options = list(LED_EFFECTS.keys())
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
    def current_option(self) -> str | None:
        """Return the currently selected LED effect."""
        return self.coordinator.data.get("led_effect_name", "Unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected LED effect."""
        if option not in LED_EFFECTS:
            _LOGGER.error(f"Invalid LED effect: {option}")
            return

        effect_value = LED_EFFECTS[option]
        
        # Get current LED settings to preserve brightness and color
        brightness = self.coordinator.data.get("led_brightness", 100)
        color_temp = self.coordinator.data.get("led_color_temp", 100)
        r = self.coordinator.data.get("led_r", 255)
        g = self.coordinator.data.get("led_g", 255)
        b = self.coordinator.data.get("led_b", 255)
        
        try:
            _LOGGER.info(f"Setting LED effect to {option} ({effect_value}) on {self.coordinator.miner_ip}")
            success = await self.coordinator.api.set_led(
                effect=effect_value,
                brightness=brightness,
                color_temp=color_temp,
                r=r,
                g=g,
                b=b,
            )
            if success:
                _LOGGER.info(f"LED effect set to {option} on {self.coordinator.miner_ip}")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to set LED effect on {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to set LED effect on {self.coordinator.miner_ip}: {err}")
            raise
