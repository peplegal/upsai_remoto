import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI buttons from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    
    device_ip = getattr(coordinator, "device_ip", "192.168.0.3")
    device_id = getattr(coordinator, "device_id", "P6IO7078YR")

    # Add the single global unlock action trigger entity button layout
    async_add_entities([UpsaiMasterUnlockButton(coordinator, session, device_ip, device_id)])


class UpsaiMasterUnlockButton(CoordinatorEntity, ButtonEntity):
    """Momentary push button to send an UNLOCK instruction to the entire unit."""
    def __init__(self, coordinator, session, ip, device_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        
        self._attr_name = "Global Unlock"
        self._attr_unique_id = f"{device_id.lower()}_master_unlock"
        self._attr_icon = "mdi:lock-open-check"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    async def async_press(self) -> None:
        """Executes a single POST request to clear all locked states globally."""
        url = f"http://{self._ip}/fwi/{self._device_id}/device/UNLOCK"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    # Force a quick coordinator refresh to clean up the locks instantly
                    await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Master UNLOCK command execution failed: %s", err)
