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
    for i in range(8):
        entities.append(UpsaiOutputSwitch(hass, coordinator, session, device_ip, device_id, i))
        entities.append(UpsaiLockSwitch(hass, coordinator, session, device_ip, device_id, i))

    entities.append(UpsaiMasterDeviceSwitch(coordinator, session, device_ip, device_id))
    async_add_entities(entities)


class UpsaiOutputSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an individual Power Outlet Switch."""
    def __init__(self, hass, coordinator, session, ip, device_id, outlet_id):
        super().__init__(coordinator)
        self.hass = hass
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._outlet_id = outlet_id
        self._local_state = None
        self._lock_time = 0  # Timestamp when the lock was engaged
        
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
        """Read state with a time-limited optimistic lock fallback."""
        server_on = False
        if self.coordinator.data and "bank" in self.coordinator.data:
            bank_str = self.coordinator.data["bank"].get("bank0_stat", "00000000")
            if len(bank_str) == 8:
                server_on = (bank_str[-1 - self._outlet_id] == "1")

        if self._local_state is not None:
            # SAFETY FILTER: If more than 4 seconds passed, the lock expired!
            if self.hass.loop.time() - self._lock_time > 4.0:
                self._local_state = None
                return server_on

            # If server caught up to user intent, cleanly release the lock
            if server_on == self._local_state:
                self._local_state = None
                return server_on
                
            return self._local_state
            
        return server_on

    async def async_turn_on(self, **kwargs) -> None:
        """Execute HTTP POST command to turn target outlet ON."""
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/ON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = True
                    self._lock_time = self.hass.loop.time()
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn on outlet %s: %s", self._outlet_id, err)
            self._local_state = None

    async def async_turn_off(self, **kwargs) -> None:
        """Execute HTTP POST command to turn target outlet OFF, checking for safety locks."""
        # 1. Read the lock bit string out of the coordinator cache right now
        is_locked = False
        if self.coordinator.data and "bank" in self.coordinator.data:
            lock_str = self.coordinator.data["bank"].get("bank0_lock", "00000000")
            if len(lock_str) == 8:
                is_locked = (lock_str[-1 - self._outlet_id] == "1")

        # 🚀 THE INSTANT REJECTION PATH FOR LOCKED SWITCHES
        if is_locked:
            url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/OFF"
            try:
                # Fire the POST action to maintain command transmission tracking logs
                await self._session.post(url)
            except Exception as err:
                _LOGGER.error("Failed to send off command to locked outlet %s: %s", self._outlet_id, err)
            
            # FORCE INSTANT REDRAW: Tell the UI framework to cancel its automatic gray-out 
            # and instantly re-evaluate our 'is_on' property right now.
            self.async_write_ha_state()
            return

        # 🎛️ THE STANDARD ADAPTIVE LOCK PATH FOR UNLOCKED SWITCHES
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/OFF"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = False
                    self._lock_time = self.hass.loop.time()
                    self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn off outlet %s: %s", self._outlet_id, err)
            self._local_state = None

class UpsaiLockSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an individual Safety Lock Toggle."""
    def __init__(self, hass, coordinator, session, ip, device_id, outlet_id):
        super().__init__(coordinator)
        self.hass = hass
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._outlet_id = outlet_id
        self._local_state = None
        self._lock_time = 0
        
        self._attr_name = f"Safety Lock {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_lock0_{outlet_id}"
        self._attr_icon = "mdi:lock"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def is_on(self) -> bool:
        server_locked = False
        if self.coordinator.data and "bank" in self.coordinator.data:
            lock_str = self.coordinator.data["bank"].get("bank0_lock", "00000000")
            if len(lock_str) == 8:
                server_locked = (lock_str[-1 - self._outlet_id] == "1")

        if self._local_state is not None:
            if self.hass.loop.time() - self._lock_time > 4.0:
                self._local_state = None
                return server_locked

            if server_locked == self._local_state:
                self._local_state = None
                return server_locked
                
            return self._local_state
            
        return server_locked

    async def async_turn_on(self, **kwargs) -> None:
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/LOCKON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    self._local_state = True
                    self._lock_time = self.hass.loop.time()
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
                    self._lock_time = self.hass.loop.time()
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
        if self._local_state is not None:
            return self._local_state
            
        if self.coordinator.data and "bank" in self.coordinator.data:
            bank_str = self.coordinator.data["bank"].get("bank0_stat", "00000000")
            lock_str = self.coordinator.data["bank"].get("bank0_lock", "00000000")
            
            if len(bank_str) == 8 and len(lock_str) == 8:
                for i in range(8):
                    if lock_str[-1 - i] == "1":
                        continue
                    if bank_str[-1 - i] == "1":
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
