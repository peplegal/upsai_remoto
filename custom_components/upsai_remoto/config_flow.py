from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remote."""
    VERSION = 1

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # Extract the dynamic 10-character serial from UPnP metadata
        device_id = discovery_info.upnp.get("modelNumber")
        
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": f"UPSAI ({device_id})"}
        
        # Move forward automatically to user confirmation
        return await self.async_step_user(user_input={"device_id": device_id})

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        if user_input is not None:
            # Explicitly save the dynamic device_id into entry memory block
            return self.async_create_entry(
                title="UPSAI Remoto", 
                data={"device_id": user_input.get("device_id")}
            )
            
        return self.async_show_form(step_id="user")
