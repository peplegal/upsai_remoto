from datetime import timedelta
import logging
import async_timeout
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UPSAI Remoto from a config entry."""
    
    # SAFE ZONE: Keeping your working IP hardcoded exactly as before
    device_ip = "192.168.0.3"
    
    # DYNAMIC VARIABLE: Pulling the discovered device ID from config flow
    device_id = entry.data.get("device_id", "P6IO7078YR")
    
    session = async_get_clientsession(hass)

    async def async_get_ups_data():
        """Fetch data from the local UPS REST API endpoints."""
        url_sensors = f"http://{device_ip}/fwi/{device_id}/sensors/values"
        url_bank = f"http://{device_ip}/fwi/{device_id}/bank/0"
        
        try:
            async with async_timeout.timeout(4):
                # 1. Fetch live telemetry metrics
                async with session.get(url_sensors) as response:
                    sensors_data = await response.json()
                
                # 2. Fetch active output/lock bank array statuses
                async with session.get(url_bank) as response:
                    bank_data = await response.json()
                
                # Combine both payloads into a unified data dictionary
                return {
                    "sensors": sensors_data,
                    "bank": bank_data.get("outlets", [])
                }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with UPS device: {err}")

    # Initialize the coordinator to poll your device every 5 seconds
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="UPSAI Data Coordinator",
        update_method=async_get_ups_data,
        update_interval=timedelta(seconds=5),
    )

    # Fetch initial data on boot before completing setup
    await coordinator.async_config_entry_first_refresh()

    # RESTORED BASELINE LINE: Keep the raw coordinator object in the array slot
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Tell Home Assistant to forward this setup to our upcoming sensor/switch files
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
