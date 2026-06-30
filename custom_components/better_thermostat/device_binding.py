"""Device binding for Better Thermostat.

Provides functions to discover all Better Thermostat instances and their
connected TRV devices by reading config-entry data, the entity registry, and
current state. Each binding record shows the BT instance, its managed TRV,
integration type, model, calibration mode, registry entry, and state.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from . import DOMAIN
from .utils.const import CONF_HEATER

_LOGGER = logging.getLogger(__name__)


@callback
def async_get_config_entry_bindings(
    hass: HomeAssistant, entry: ConfigEntry
) -> list[dict[str, Any]]:
    """Return all TRVs bound to a single Better Thermostat config entry.

    Each item in the returned list represents one TRV that the BT instance
    discovered and controls.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    entry : ConfigEntry
        A Better Thermostat config entry.

    Returns
    -------
    list[dict[str, Any]]
        A list of TRV binding records with keys:
            - ``bt_entry_id`` — the config entry id of the BT instance.
            - ``bt_name`` — the display name of the BT instance.
            - ``trv_entity_id`` — the entity id of the bound TRV.
            - ``integration`` — the adapter integration type
              (generic / tado / mqtt / deconz).
            - ``model`` — the TRV model identifier.
            - ``calibration_mode`` — the active calibration mode.
            - ``registry_entry`` — the entity registry entry (or ``None``
              if unregistered).
            - ``state`` — the current HA state of the TRV entity (or
              ``None`` if unavailable).
    """
    conf = entry.data
    heaters = conf.get(CONF_HEATER) or []
    if not heaters:
        _LOGGER.debug(
            "better_thermostat %s: no TRVs in config entry %s",
            conf.get("name", entry.title),
            entry.entry_id,
        )
        return []

    registry = er.async_get(hass)
    bindings = []

    for trv_conf in heaters:
        entity_id = trv_conf.get("trv")
        if not entity_id:
            continue

        reg_entry = registry.async_get(entity_id)
        state = hass.states.get(entity_id)

        advanced = trv_conf.get("advanced") or {}
        bindings.append(
            {
                "bt_entry_id": entry.entry_id,
                "bt_name": conf.get("name", entry.title),
                "trv_entity_id": entity_id,
                "integration": trv_conf.get("integration"),
                "model": trv_conf.get("model"),
                "calibration_mode": advanced.get("calibration_mode"),
                "registry_entry": reg_entry,
                "state": state,
            }
        )

    return bindings


@callback
def async_get_all_bindings(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Return all TRVs bound to every Better Thermostat instance.

    Iterates every Better Thermostat config entry currently loaded and
    collects the device binding records. This is the entry point for
    diagnostics, services, or API handlers that need a full inventory
    of BT-managed devices.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.

    Returns
    -------
    list[dict[str, Any]]
        Concatenated binding records from every active BT config entry.
    """
    all_bindings = []

    for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
        if "climate" not in entry_data:
            continue
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            continue
        all_bindings.extend(async_get_config_entry_bindings(hass, entry))

    return all_bindings
