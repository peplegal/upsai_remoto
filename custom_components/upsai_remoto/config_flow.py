from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remote."""
    VERSION = 1

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # 1. Pull the unique hardware serial number from the UPnP metadata
        device_id = discovery_info.upnp.get("modelNumber")
        
        # 2. Extract the clean, raw IP string directly out of the network headers
        # This safely pulls a pure string like "192.168.0.3" bypassing URL splitting bugs
        device_ip = discovery_info.ssdp_headers.get("_host")
        
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": f"UPSAI ({device_id})"}
        
        # Pass both clean variables forward to the confirmation save step
        return await self.async_step_user(user_input={"device_id": device_id, "ip": device_ip})

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        if user_input is not None:
            # Securely save the dynamic IP and Serial into the config entry storage registry
            return self.async_create_entry(
                title=f"UPSAI Remote ({user_input.get('device_id')})", 
                data={
                    "device_id": user_input.get("device_id"),
                    "ip": user_input.get("ip")
                }
            )
            
        return self.async_show_form(step_id="user")
