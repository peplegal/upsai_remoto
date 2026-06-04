import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI buttons from a config entry."""
    engine = hass.data[DOMAIN][entry.entry_id]
    device_id = getattr(engine, "device_id", "P6IO7078YR")

    # 1. Initialize the entity array with the Master Unlock button
    entities = [UpsaiMasterUnlockButton(engine, device_id)]

    # 2. Loop from 0 to 7 to safely generate the 8 individual Reboot buttons
    for i in range(8):
        entities.append(UpsaiOutletRebootButton(engine, device_id, i))

    # 3. Add all 9 button entities to Home Assistant simultaneously
    async_add_entities(entities)


class UpsaiMasterUnlockButton(ButtonEntity):
    """Momentary push button to send a prefixed UNLOCK instruction."""
    def __init__(self, engine, device_id):
        self._engine = engine
        self._device_id = device_id
        
        self._attr_name = "Destravar"
        self._attr_unique_id = f"{device_id.lower()}_master_unlock"
        self._attr_icon = "mdi:lock-open-check"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"UPSAI Remote {device_id}",
            manufacturer="UPSAI Sistemas de Energia",
            model="FWI",
        )

    async def async_added_to_hass(self) -> None:
        """Register our redraw hook directly into the custom WebSocket engine pool."""
        self._engine.async_add_listener(self.async_write_ha_state)

    async def async_press(self) -> None:
        """Executes a single string write request prefixed with HA_."""
        await self._engine.async_send_ws_command("HA_DEV:UNLOCK")


class UpsaiOutletRebootButton(ButtonEntity):
    """Momentary push button to cycle power on an individual outlet."""
    def __init__(self, engine, device_id, outlet_id):
        self._engine = engine
        self._device_id = device_id
        self._outlet_id = outlet_id
        
        # User-friendly description that maps seamlessly to the Device Card registry
        self._attr_name = f"Reiniciar {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_reboot0_{outlet_id}"
        self._attr_icon = "mdi:restart"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        """Register our redraw hook directly into the custom WebSocket engine pool."""
        self._engine.async_add_listener(self.async_write_ha_state)

    async def async_press(self) -> None:
        """Fires the precise upstream REBOOT text token down the open pipe string channel."""
        await self._engine.async_send_ws_command(f"HA_OUT0-{self._outlet_id}:REBOOT")