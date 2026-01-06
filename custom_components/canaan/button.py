"""Support for Canaan Avalon Miner buttons."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canaan buttons from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        CanaanUpdateButton(coordinator),
        CanaanRebootButton(coordinator),
    ]

    async_add_entities(entities)


class CanaanUpdateButton(CoordinatorEntity, ButtonEntity):
    """Representation of Canaan Avalon Miner manual update button."""

    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_update"
        self._attr_name = "Update"
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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available

    async def async_press(self) -> None:
        """Handle the button press - trigger immediate update."""
        _LOGGER.info(f"Manual update requested for miner at {self.coordinator.miner_ip}")
        await self.coordinator.async_request_refresh()
        _LOGGER.info(f"Manual update completed for miner at {self.coordinator.miner_ip}")


class CanaanRebootButton(CoordinatorEntity, ButtonEntity):
    """Representation of Canaan Avalon Miner reboot button."""

    _attr_icon = "mdi:restart"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data['mac']}_reboot"
        self._attr_name = "Reboot"
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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available

    async def async_press(self) -> None:
        """Handle the button press - reboot the miner."""
        _LOGGER.info(f"Reboot requested for miner at {self.coordinator.miner_ip}")
        success = await self.coordinator.api.reboot()
        if success:
            _LOGGER.info(f"Reboot command sent to miner at {self.coordinator.miner_ip}")
        else:
            _LOGGER.error(f"Failed to send reboot command to miner at {self.coordinator.miner_ip}")
