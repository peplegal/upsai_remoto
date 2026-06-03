import logging
from homeassistant.components.switch import SwitchEntity
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
    """Set up the UPSAI switches from a config entry."""
    config_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data["coordinator"]
    device_ip = config_data["ip"]
    device_id = config_data["device_id"]
    
    session = async_get_clientsession(hass)

    entities = []
    for i in range(8):
        entities.append(UpsaiOutputSwitch(coordinator, session, device_ip, device_id, i))
        entities.append(UpsaiLockSwitch(coordinator, session, device_ip, device_id, i))

    async_add_entities(entities)


class UpsaiOutputSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an individual Power Outlet Switch."""
    def __init__(self, coordinator, session, ip, device_id, outlet_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._outlet_id = outlet_id
        self._local_state = None  # Local optimistic state tracker
        
        self._attr_name = f"Saída {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_out0_{outlet_id}"
        self._attr_icon = "mdi:power-socket-us"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"UPSAI Remote {device_id}",
            manufacturer="UPSAI Sistemas de Energia",
            model="FWI",
        )

    @property
    def is_on(self) -> bool:
        """Read state with immediate optimistic local override support."""
        if self._local_state is not None:
            return self._local_state
            
        if self.coordinator.data and "bank" in self.coordinator.data:
            outlets = self.coordinator.data["bank"]
            for outlet in outlets:
                if outlet.get("id") == self._outlet_id:
                    return outlet.get("state") == "ON"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/ON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    # 1. Update the local state instantly in memory
                    self._local_state = True
                    # 2. Tell the UI to redraw immediately with no network lag
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn on outlet %s: %s", self._outlet_id, err)
        finally:
            # Clear the optimistic lock so the next 5s polling cycle resumes control
            self._local_state = None

    async def async_turn_off(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/OFF"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = False
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn off outlet %s: %s", self._outlet_id, err)
        finally:
            self._local_state = None


class UpsaiLockSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an individual Safety Lock Toggle."""
    def __init__(self, coordinator, session, ip, device_id, outlet_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._outlet_id = outlet_id
        self._local_state = None
        
        self._attr_name = f"Safety Lock {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_lock0_{outlet_id}"
        self._attr_icon = "mdi:lock"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def is_on(self) -> bool:
        if self._local_state is not None:
            return self._local_state
            
        if self.coordinator.data and "bank" in self.coordinator.data:
            outlets = self.coordinator.data["bank"]
            for outlet in outlets:
                if outlet.get("id") == self._outlet_id:
                    return outlet.get("locked") is True
        return False

    async def async_turn_on(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/LOCKON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = True
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to lock outlet %s: %s", self._outlet_id, err)
        finally:
            self._local_state = None

    async def async_turn_off(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/UNLOCK"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = False
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to unlock outlet %s: %s", self._outlet_id, err)
        finally:
            self._local_state = None
