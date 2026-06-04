import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.add_entities import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI buttons from a config entry."""
    # This now safely extracts our custom EventDrivenDeviceEngine object
    engine = hass.data[DOMAIN][entry.entry_id]
    device_id = getattr(engine, "device_id", "P6IO7078YR")

    async_add_entities([UpsaiMasterUnlockButton(engine, device_id)])


class UpsaiMasterUnlockButton(ButtonEntity):
    """Momentary push button to send a prefixed UNLOCK instruction."""
    def __init__(self, engine, device_id):
        """Initialize the button with our pure event engine."""
        self._engine = engine
        self._device_id = device_id
        
        self._attr_name = "Global Unlock"
        self._attr_unique_id = f"{device_id.lower()}_master_unlock"
        self._attr_icon = "mdi:lock-open-check"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        """Register our redraw hook directly into the custom WebSocket engine pool."""
        self._engine.async_add_listener(self.async_write_ha_state)

    async def async_press(self) -> None:
        """Executes a single string write request prefixed with HA_."""
        await self._engine.async_send_ws_command("HA_DEV:UNLOCK")