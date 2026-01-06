"""Support for Canaan Avalon Miner switches."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_NANO3S, MODEL_Q

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canaan switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    model_type = coordinator.model_type

    entities = []
    
    # Power switch for Mini 3 and Q (not supported on Nano 3s)
    if model_type != MODEL_NANO3S:
        entities.append(CanaanPowerSwitch(coordinator))

    async_add_entities(entities)


class CanaanPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of Canaan Avalon Miner power control switch."""

    _attr_icon = "mdi:power"

    def __init__(self, coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_power_control"
        self._attr_name = "Power"
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
    def is_on(self) -> bool:
        """Return true if the miner is powered on (state is Working or Initializing)."""
        state_num = self.coordinator.data.get("state_num", 0)
        # Consider miner "on" if state is Working (1) or Initializing (0)
        # This handles the transition period after power-on when miner is starting up
        return state_num in [0, 1]  # Initializing or Working

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the miner."""
        try:
            _LOGGER.info(f"Turning on miner at {self.coordinator.miner_ip}")
            success = await self.coordinator.api.turn_on()
            if success:
                _LOGGER.info(f"Miner at {self.coordinator.miner_ip} turned on")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to turn on miner at {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to turn on miner at {self.coordinator.miner_ip}: {err}")
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the miner."""
        try:
            _LOGGER.info(f"Turning off miner at {self.coordinator.miner_ip}")
            success = await self.coordinator.api.turn_off()
            if success:
                _LOGGER.info(f"Miner at {self.coordinator.miner_ip} turned off")
                # Wait 1 second for miner to process command, then refresh
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to turn off miner at {self.coordinator.miner_ip}")
        except Exception as err:
            _LOGGER.error(f"Failed to turn off miner at {self.coordinator.miner_ip}: {err}")
            raise
