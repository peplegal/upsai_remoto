import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI buttons from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_id = getattr(coordinator, "device_id", "P6IO7078YR")

    async_add_entities([UpsaiMasterUnlockButton(coordinator, device_id)])


class UpsaiMasterUnlockButton(CoordinatorEntity, ButtonEntity):
    """Momentary push button to send a prefixed UNLOCK instruction."""
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._device_id = device_id
        
        self._attr_name = "Global Unlock"
        self._attr_unique_id = f"{device_id.lower()}_master_unlock"
        self._attr_icon = "mdi:lock-open-check"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        """Register listener to redraw the UI instantly on packet arrival."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_press(self) -> None:
        """Executes a single string write request prefixed with HA_."""
        await self._coordinator.async_send_ws_command("HA_DEV:UNLOCK")
