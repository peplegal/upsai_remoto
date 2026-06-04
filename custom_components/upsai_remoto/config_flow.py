import logging
from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remote."""
    VERSION = 1

    def __init__(self):
        """Initialize the tracking variables inside the class context layer."""
        self._device_id = None
        self._device_ip = None
        self._model_name = "FWI"
        self._model_number = "1200"

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # 1. Safely extract all required XML string tags on the very first network touch
        self._device_id = discovery_info.upnp.get("serialNumber") or discovery_info.upnp.get("modelNumber")
        self._device_ip = discovery_info.ssdp_headers.get("_host")
        self._model_name = discovery_info.upnp.get("modelName") or "FWI"
        self._model_number = discovery_info.upnp.get("modelNumber") or "1200"
        
        # DHCP TRACKING SHIELD: Update the registry entry automatically if the IP changes
        current_entry = self._async_current_entry()
        if current_entry and current_entry.unique_id == self._device_id:
            if current_entry.data.get("ip") != self._device_ip:
                _LOGGER.info("SSDP network update: Device %s moved to new IP %s", self._device_id, self._device_ip)
                self.hass.config_entries.async_update_entry(
                    current_entry, 
                    data={**current_entry.data, "ip": self._device_ip}
                )
            return self.async_abort(reason="already_configured")
                        
        await self.async_set_unique_id(self._device_id)
        self._abort_if_unique_id_configured()

        # Save the real dynamic variables straight into the persistent context dictionary layer
        self.context["discovery_info"] = {
            "device_id": self._device_id,
            "ip": self._device_ip,
            "model_name": self._model_name,
            "model_number": self._model_number
        }

        self.context["title_placeholders"] = {"name": f"UPSAI ({self._device_id})"}
        
        # Advance cleanly to the user confirmation step form
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        # Recover our verified data out of the secure context dictionary layer
        discovery_data = self.context.get("discovery_info", {})
        device_id = discovery_data.get("device_id")
        device_ip = discovery_data.get("ip")
        
        # Security guard block: stop manual blank configuration attempts
        if not device_id or not device_ip:
            return self.async_abort(reason="cannot_connect")

        # 🚀 THE CRITICAL FIX: Only save the entry when user_input is NOT None.
        # This guarantees it waits for the user to physically click "Submit" on the form wizard screen!
        if user_input is not None:
            model_name = discovery_data.get("model_name") or "FWI"
            model_number = discovery_data.get("model_number") or "1200"
            full_model_string = f"{model_name} {model_number}".strip()

            _LOGGER.info("Successfully committing dynamic entry: ID=%s, IP=%s, Model=%s", device_id, device_ip, full_model_string)

            return self.async_create_entry(
                title=f"UPSAI Remote ({device_id})", 
                data={
                    "device_id": device_id,
                    "ip": device_ip,         # Written safely with 100% data persistence!
                    "model": full_model_string
                }
            )
            
        return self.async_show_form(step_id="user")
