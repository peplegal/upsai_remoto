from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remote."""
    VERSION = 1

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # Pulls your unique hardware serial number from the XML metadata
        device_id = discovery_info.upnp.get("modelNumber")
        device_ip = discovery_info.ssdp_location
        
        # Sets the unique ID so Home Assistant handles duplicates gracefully
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        # Passes variables into the visual user setup form parameters
        self.context["title_placeholders"] = {"name": f"UPSAI ({device_id})"}
        
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        if user_input is not None:
            return self.async_create_entry(title="UPSAI Remoto", data={})
            
        return self.async_show_form(step_id="user")
