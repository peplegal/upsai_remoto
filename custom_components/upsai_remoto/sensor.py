from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "upsai_remoto"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Automatically generate and append the 4 sensor classes
    async_add_entities([
        UpsaiVoltageSensor(coordinator, "Vin", "Input Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:sine-wave"),
        UpsaiVoltageSensor(coordinator, "Vout", "Output Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:lightning-bolt"),
        UpsaiGenericSensor(coordinator, "Power", "Power Load", "%", "mdi:gauge"),
        UpsaiTextSensor(coordinator, "Msg", "Status Message", "mdi:information-outline")
    ])

class UpsaiVoltageSensor(CoordinatorEntity, SensorEntity):
    """Representation of an electrical Voltage Sensor."""
    def __init__(self, coordinator, key, name, device_class, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"p6io7078yr_{key.lower()}"

    @property
    def native_value(self):
        """Return the current numerical reading from cache."""
        return self.coordinator.data["sensors"].get(self._key)

class UpsaiGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a numeric Percentage/Load Sensor."""
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"p6io7078yr_{key.lower()}"

    @property
    def native_value(self):
        return self.coordinator.data["sensors"].get(self._key)

class UpsaiTextSensor(CoordinatorEntity, SensorEntity):
    """Representation of a plain Text Status string."""
    def __init__(self, coordinator, key, name, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"p6io7078yr_{key.lower()}"

    @property
    def native_value(self):
        return self.coordinator.data["sensors"].get(self._key)
