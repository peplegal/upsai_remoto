from urllib.parse import urlparse
from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remoto."""
    VERSION = 1

    def __init__(self):
        """Initialize the flow storage variables."""
        self._device_id = None
        self._device_ip = None

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # 1. Pull the unique hardware serial number from the XML metadata
        self._device_id = discovery_info.upnp.get("modelNumber")
        
        # 2. Extract the raw IP address out of the location URL
        # Example: transforms "http://192.168.0" into "192.168.0.3"
        parsed_url = urlparse(discovery_info.ssdp_location)
        self._device_ip = parsed_url.hostname
        
        # Set the unique ID so Home Assistant handles duplicates gracefully
        await self.async_set_unique_id(self._device_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": f"UPSAI ({self._device_id})"}
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        if user_input is not None or self.context.get("source") == config_entries.SOURCE_SSDP:
            return self.async_create_entry(
                title=f"UPSAI Remote ({self._device_id})", 
                data={
                    "ip": self._device_ip,
                    "device_id": self._device_id
                }
            )
            
        return self.async_show_form(step_id="user")
