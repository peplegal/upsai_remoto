import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI switches from a config entry."""
    # Safely extract our custom EventDrivenDeviceEngine object
    engine = hass.data[DOMAIN][entry.entry_id]
    device_id = getattr(engine, "device_id", "P6IO7078YR")

    entities = []
    for i in range(8):
        entities.append(UpsaiOutputSwitch(engine, device_id, i))
        entities.append(UpsaiLockSwitch(engine, device_id, i))

    entities.append(UpsaiMasterDeviceSwitch(engine, device_id))
    async_add_entities(entities)


class UpsaiOutputSwitch(SwitchEntity):
    """Representation of an individual Power Outlet Switch."""
    def __init__(self, engine, device_id, outlet_id):
        self._engine = engine
        self._device_id = device_id
        self._outlet_id = outlet_id
        
        self._attr_name = f"Saída {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_out0_{outlet_id}"
        self._attr_icon = "mdi:power-socket-us"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"UPSAI Remote {device_id}",
            manufacturer="UPSAI Sistemas de Energia",
            model="FWI",
        )

    async def async_added_to_hass(self) -> None:
        """Register listener to redraw the UI instantly on packet arrival."""
        self._engine.async_add_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Read state right-to-left from the engine memory state tracker cache."""
        if self._engine.data and "bank" in self._engine.data:
            bank_str = self._engine.data["bank"].get("bank0_stat", "00000000")
            if len(bank_str) == 8:
                return bank_str[-1 - self._outlet_id] == "1"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._engine.async_send_ws_command(f"HA_OUT0-{self._outlet_id}:ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self._engine.async_send_ws_command(f"HA_OUT0-{self._outlet_id}:OFF")


class UpsaiLockSwitch(SwitchEntity):
    """Representation of an individual Safety Lock Toggle."""
    def __init__(self, engine, device_id, outlet_id):
        self._engine = engine
        self._device_id = device_id
        self._outlet_id = outlet_id
        
        self._attr_name = f"Safety Lock {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_lock0_{outlet_id}"
        self._attr_icon = "mdi:lock"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        self._engine.async_add_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        if self._engine.data and "bank" in self._engine.data:
            lock_str = self._engine.data["bank"].get("bank0_lock", "00000000")
            if len(lock_str) == 8:
                return lock_str[-1 - self._outlet_id] == "1"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._engine.async_send_ws_command(f"HA_OUT0-{self._outlet_id}:LOCKON")

    async def async_turn_off(self, **kwargs) -> None:
        await self._engine.async_send_ws_command(f"HA_OUT0-{self._outlet_id}:UNLOCK")


class UpsaiMasterDeviceSwitch(SwitchEntity):
    """Representation of the Global Device Master Toggle Switch."""
    def __init__(self, engine, device_id):
        self._engine = engine
        self._device_id = device_id
        
        self._attr_name = "Dispositivo"
        self._attr_unique_id = f"{device_id.lower()}_master_device"
        self._attr_icon = "mdi:power-matrix"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        self._engine.async_add_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        if self._engine.data and "bank" in self._engine.data:
            bank_str = self._engine.data["bank"].get("bank0_stat", "00000000")
            lock_str = self._engine.data["bank"].get("bank0_lock", "00000000")
            
            if len(bank_str) == 8 and len(lock_str) == 8:
                for i in range(8):
                    if lock_str[-1 - i] == "1":
                        continue
                    if bank_str[-1 - i] == "1":
                        return True
        return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._engine.async_send_ws_command("HA_DEV:ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self._engine.async_send_ws_command("HA_DEV:OFF")