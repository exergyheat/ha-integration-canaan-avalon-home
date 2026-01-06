"""Support for Canaan Avalon Miner sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_MINI3, MODEL_NANO3S, MODEL_Q, TERA_HASH_PER_SECOND

_LOGGER = logging.getLogger(__name__)

# Common sensor descriptions (all models)
SENSOR_TYPES_COMMON: dict[str, SensorEntityDescription] = {
    "hashrate": SensorEntityDescription(
        key="hashrate",
        name="Hashrate",
        native_unit_of_measurement=TERA_HASH_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    "output_temp": SensorEntityDescription(
        key="output_temp",
        name="Output Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "fan_percentage": SensorEntityDescription(
        key="fan_percentage",
        name="Fan Speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan",
    ),
    "state": SensorEntityDescription(
        key="state",
        name="State",
        icon="mdi:state-machine",
    ),
    "mode": SensorEntityDescription(
        key="mode",
        name="Work Mode",
        icon="mdi:wrench",
    ),
}

# Mini 3 specific sensors
SENSOR_TYPES_MINI3: dict[str, SensorEntityDescription] = {
    "internal_temp": SensorEntityDescription(
        key="internal_temp",
        name="Ambient Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hb_temp": SensorEntityDescription(
        key="hb_temp",
        name="Hash Board Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "max_temp": SensorEntityDescription(
        key="max_temp",
        name="Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "avg_temp": SensorEntityDescription(
        key="avg_temp",
        name="Average Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "power": SensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "level": SensorEntityDescription(
        key="level",
        name="Work Level",
        icon="mdi:speedometer",
    ),
}

# Nano 3s specific sensors
SENSOR_TYPES_NANO3S: dict[str, SensorEntityDescription] = {
    "max_temp": SensorEntityDescription(
        key="max_temp",
        name="Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "avg_temp": SensorEntityDescription(
        key="avg_temp",
        name="Average Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "target_temp": SensorEntityDescription(
        key="target_temp",
        name="Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    "fan_rpm": SensorEntityDescription(
        key="fan_rpm",
        name="Fan RPM",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan",
        entity_registry_enabled_default=False,
    ),
    "power": SensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "elapsed": SensorEntityDescription(
        key="elapsed",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
    ),
}

# Avalon Q specific sensors
SENSOR_TYPES_Q: dict[str, SensorEntityDescription] = {
    "internal_temp": SensorEntityDescription(
        key="internal_temp",
        name="Ambient Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hb_internal_temp": SensorEntityDescription(
        key="hb_internal_temp",
        name="Hash Board Internal Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hb_output_temp": SensorEntityDescription(
        key="hb_output_temp",
        name="Hash Board Output Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "max_temp": SensorEntityDescription(
        key="max_temp",
        name="Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "avg_temp": SensorEntityDescription(
        key="avg_temp",
        name="Average Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "wifi_rssi": SensorEntityDescription(
        key="wifi_rssi",
        name="WiFi Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    "power": SensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "level": SensorEntityDescription(
        key="level",
        name="Work Level",
        icon="mdi:speedometer",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canaan sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    model_type = coordinator.model_type

    entities = []

    # Add common sensors (all models)
    for sensor_key, description in SENSOR_TYPES_COMMON.items():
        # Skip "mode" sensor for Q (it doesn't have work modes, only levels)
        if model_type == MODEL_Q and sensor_key == "mode":
            continue
        entities.append(
            CanaanSensor(
                coordinator=coordinator,
                description=description,
                sensor_key=sensor_key,
            )
        )

    # Add model-specific sensors
    if model_type == MODEL_NANO3S:
        # Nano 3s specific sensors
        for sensor_key, description in SENSOR_TYPES_NANO3S.items():
            entities.append(
                CanaanSensor(
                    coordinator=coordinator,
                    description=description,
                    sensor_key=sensor_key,
                )
            )
    elif model_type == MODEL_Q:
        # Avalon Q specific sensors
        for sensor_key, description in SENSOR_TYPES_Q.items():
            entities.append(
                CanaanSensor(
                    coordinator=coordinator,
                    description=description,
                    sensor_key=sensor_key,
                )
            )
    else:
        # Mini 3 specific sensors
        for sensor_key, description in SENSOR_TYPES_MINI3.items():
            entities.append(
                CanaanSensor(
                    coordinator=coordinator,
                    description=description,
                    sensor_key=sensor_key,
                )
            )

    async_add_entities(entities)


class CanaanSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Canaan Avalon Miner sensor."""

    def __init__(
        self,
        coordinator,
        description: SensorEntityDescription,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_key = sensor_key
        self._attr_unique_id = f"{coordinator.data['mac']}_{sensor_key}"
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
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor_key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success
