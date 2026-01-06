"""The Canaan Avalon Miner integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_IP,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODEL_NAMES,
    MODEL_UNKNOWN,
    PLATFORMS,
)
from .coordinator import CanaanCoordinator, detect_model

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Canaan from a config entry."""
    miner_ip = entry.data[CONF_IP]
    # Use entry.title as the device name (this is what user sets in config flow)
    miner_name = entry.title
    
    # Get options (with fallback to entry data for backwards compatibility)
    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    
    # Get model info from config entry, or detect if not present (migration)
    model_type = entry.data.get(CONF_MODEL)
    model_name = entry.data.get("model_name")
    
    # Always re-detect model to ensure accuracy and handle firmware updates
    _LOGGER.info(f"Detecting model at {miner_ip}")
    detected_model_type, detected_model_name = await detect_model(miner_ip, port)
    
    # If model detection succeeded and differs from stored model, update config entry
    if detected_model_type != MODEL_UNKNOWN and detected_model_type != model_type:
        _LOGGER.warning(
            f"Model mismatch detected at {miner_ip}: "
            f"stored={model_type} ({model_name}), "
            f"detected={detected_model_type} ({detected_model_name}). "
            f"Updating config entry to detected model."
        )
        # Update the config entry with correct model info
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_MODEL: detected_model_type,
                "model_name": detected_model_name,
            },
        )
        model_type = detected_model_type
        model_name = detected_model_name
    elif detected_model_type != MODEL_UNKNOWN:
        # Detection succeeded, use detected values
        model_type = detected_model_type
        model_name = detected_model_name
    elif not model_type:
        # Detection failed and no stored model - use unknown
        _LOGGER.warning(f"Could not detect model at {miner_ip}, using stored or default values")
        model_type = MODEL_UNKNOWN
        model_name = "Avalon Miner"
    
    if not model_name:
        model_name = MODEL_NAMES.get(model_type, "Avalon Miner")
    
    _LOGGER.info(f"Setting up {model_name}: {miner_name} at {miner_ip}")
    
    # Create coordinator with model info
    coordinator = CanaanCoordinator(
        hass=hass,
        ip=miner_ip,
        port=port,
        scan_interval=scan_interval,
        name=miner_name,
        model_type=model_type,
        model_name=model_name,
    )
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Request immediate refresh to populate entity states
    await coordinator.async_request_refresh()
    
    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
