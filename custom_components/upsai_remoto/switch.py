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
    coordinator = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    
    device_ip = getattr(coordinator, "device_ip", "192.168.0.3")
    device_id = getattr(coordinator, "device_id", "P6IO7078YR")

    entities = []
    # 1. Register the 8 individual outlet pairs
    for i in range(8):
        entities.append(UpsaiOutputSwitch(coordinator, session, device_ip, device_id, i))
        entities.append(UpsaiLockSwitch(coordinator, session, device_ip, device_id, i))

    # 2. Append the new Master Device Switch to the card registration grid
    entities.append(UpsaiMasterDeviceSwitch(coordinator, session, device_ip, device_id))

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
        self._local_state = None
        
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
            # Pull the 8-character string token directly from the cache
            bank_str = self.coordinator.data["bank"].get("bank0_stat", "00000000")
            
            # Verify the index exists and return True if it equals "1"
            if len(bank_str) > self._outlet_id:
                return bank_str[self._outlet_id] == "1"
                
        return False

    async def async_turn_on(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/ON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = True
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn on outlet %s: %s", self._outlet_id, err)
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
            lock_str = self.coordinator.data["bank"].get("bank0_lock", "00000000")
            
            if len(lock_str) > self._outlet_id:
                return lock_str[self._outlet_id] == "1"
                
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
        self._local_state = None


class UpsaiMasterDeviceSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Global Device Master Toggle Switch."""
    def __init__(self, coordinator, session, ip, device_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._local_state = None
        
        self._attr_name = "Dispositivo"
        self._attr_unique_id = f"{device_id.lower()}_master_device"
        self._attr_icon = "mdi:power-matrix"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def is_on(self) -> bool:
        """Determines if the global toggle is ON by ignoring locked elements."""
        if self._local_state is not None:
            return self._local_state
            
        if self.coordinator.data and "bank" in self.coordinator.data:
            bank_str = self.coordinator.data["bank"].get("bank0_stat", "00000000")
            lock_str = self.coordinator.data["bank"].get("bank0_lock", "00000000")
            
            # Loop from index 0 to 7
            for i in range(min(len(bank_str), len(lock_str), 8)):
                # If the safety lock is engaged ("1"), skip evaluating this channel
                if lock_str[i] == "1":
                    continue
                # If an unlocked channel is active ("1"), return True immediately
                if bank_str[i] == "1":
                    return True
                    
        return False

    async def async_turn_on(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/device/ON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = True
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Master ON action failed: %s", err)
        self._local_state = None

    async def async_turn_off(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/device/OFF"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = False
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Master OFF action failed: %s", err)
        self._local_state = None
