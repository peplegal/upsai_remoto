from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "upsai_remoto"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UPSAI sensors from a config entry."""
    # Safely extract our custom EventDrivenDeviceEngine object
    engine = hass.data[DOMAIN][entry.entry_id]
    device_id = getattr(engine, "device_id", "P6IO7078YR")

    async_add_entities([
        UpsaiVoltageSensor(engine, device_id, "Vin", "Input Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:sine-wave"),
        UpsaiVoltageSensor(engine, device_id, "Vout", "Output Voltage", SensorDeviceClass.VOLTAGE, "V", "mdi:lightning-bolt"),
        UpsaiGenericSensor(engine, device_id, "Power", "Power Load", "%", "mdi:gauge"),
        UpsaiTextSensor(engine, device_id, "Msg", "Status Message", "mdi:information-outline")
    ])


class UpsaiVoltageSensor(SensorEntity):
    """Representation of an electrical Voltage Sensor."""
    def __init__(self, engine, device_id, key, name, device_class, unit, icon):
        self._engine = engine
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
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
    def native_value(self):
        """Read values directly from the event-driven engine memory space."""
        if self._engine.data and "sensors" in self._engine.data:
            return self._engine.data["sensors"].get(self._key)
        return None


class UpsaiGenericSensor(SensorEntity):
    """Representation of a numeric Percentage/Load Sensor."""
    def __init__(self, engine, device_id, key, name, unit, icon):
        self._engine = engine
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        self._engine.async_add_listener(self.async_write_ha_state)

    @property
    def native_value(self):
        if self._engine.data and "sensors" in self._engine.data:
            return self._engine.data["sensors"].get(self._key)
        return None


class UpsaiTextSensor(SensorEntity):
    """Representation of a plain Text Status string."""
    def __init__(self, engine, device_id, key, name, icon):
        self._engine = engine
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id.lower()}_{key.lower()}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        self._engine.async_add_listener(self.async_write_ha_state)

    @property
    def native_value(self):
        if self._engine.data and "sensors" in self._engine.data:
            return self._engine.data["sensors"].get(self._key)
        return None