from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # DYNAMIC VARIABLE FETCH: Extracts your 10-char Serial ID from Home Assistant storage
    # If it fails to find it, it defaults back to your working baseline serial string.
    device_id = entry.unique_id or "P6IO7078YR"

    async_add_entities([
        UpsaiVoltageSensor(coordinator, device_id, "Vin", "Input Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:sine-wave"),
        UpsaiVoltageSensor(coordinator, device_id, "Vout", "Output Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:lightning-bolt"),
        UpsaiGenericSensor(coordinator, device_id, "Power", "Power Load", "%", "mdi:gauge"),
        UpsaiTextSensor(coordinator, device_id, "Msg", "Status Message", "mdi:information-outline")
    ])

class UpsaiVoltageSensor(CoordinatorEntity, SensorEntity):
    """Representation of an electrical Voltage Sensor."""
    def __init__(self, coordinator, device_id, key, name, device_class, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        # Dynamically inject the correct lower-case unique ID key string mapping
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"UPSAI Remote {device_id}",
            manufacturer="UPSAI Sistemas de Energia",
            model="FWI",
        )

    @property
    def native_value(self):
        if self.coordinator.data and "sensors" in self.coordinator.data:
            return self.coordinator.data["sensors"].get(self._key)
        return None

class UpsaiGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a numeric Percentage/Load Sensor."""
    def __init__(self, coordinator, device_id, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def native_value(self):
        if self.coordinator.data and "sensors" in self.coordinator.data:
            return self.coordinator.data["sensors"].get(self._key)
        return None

class UpsaiTextSensor(CoordinatorEntity, SensorEntity):
    """Representation of a plain Text Status string."""
    def __init__(self, coordinator, device_id, key, name, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def native_value(self):
        if self.coordinator.data and "sensors" in self.coordinator.data:
            return self.coordinator.data["sensors"].get(self._key)
        return None
