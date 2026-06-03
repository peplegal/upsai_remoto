import logging
import aiohttp
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    
    # Prototyping fallbacks (Will match dynamic code later)
    device_ip = "192.168.0.3"
    device_id = "P6IO7078YR"

    entities = []
    
    # Loop from 0 to 7 to generate all 16 switches cleanly
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
        
        # User-friendly rendering configurations
        self._attr_name = f"Saída {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_out0_{outlet_id}"
        self._attr_icon = "mdi:power-socket-us"

    @property
    def is_on(self) -> bool:
        """Read the live state array directly from the flat coordinator array cache."""
        if self.coordinator.data and "bank" in self.coordinator.data:
            outlets = self.coordinator.data["bank"]  # Corrected line
            for outlet in outlets:
                if outlet.get("id") == self._outlet_id:
                    return outlet.get("state") == "ON"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Execute HTTP POST command to turn target outlet ON."""
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/ON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    # Force a prompt cache update to show the switch turned on instantly
                    await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on outlet %s: %s", self._outlet_id, err)

    async def async_turn_off(self, **kwargs) -> None:
        """Execute HTTP POST command to turn target outlet OFF."""
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/OFF"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off outlet %s: %s", self._outlet_id, err)


class UpsaiLockSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an individual Safety Lock Toggle."""
    
    def __init__(self, coordinator, session, ip, device_id, outlet_id):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._session = session
        self._ip = ip
        self._device_id = device_id
        self._outlet_id = outlet_id
        
        self._attr_name = f"Safety Lock {outlet_id}"
        self._attr_unique_id = f"{device_id.lower()}_lock0_{outlet_id}"
        self._attr_icon = "mdi:lock"

    @property
    def is_on(self) -> bool:
        """Read the live lock boolean directly from the flat coordinator array cache."""
        if self.coordinator.data and "bank" in self.coordinator.data:
            outlets = self.coordinator.data["bank"]  # Corrected line
            for outlet in outlets:
                if outlet.get("id") == self._outlet_id:
                    return outlet.get("locked") is True
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Execute HTTP POST command to engage LOCKON status."""
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/LOCKON"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to lock outlet %s: %s", self._outlet_id, err)

    async def async_turn_off(self, **kwargs) -> None:
        """Execute HTTP POST command to trigger UNLOCK status."""
        url = f"http://{self._ip}/fwi/{self._device_id}/output/0/{self._outlet_id}/UNLOCK"
        try:
            async with self._session.post(url) as response:
                if response.status == 200:
                    await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to unlock outlet %s: %s", self._outlet_id, err)
