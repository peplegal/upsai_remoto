import logging
from homeassistant import config_entries
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

class UpsaiRemotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UPSAI Remote."""
    VERSION = 1

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        # 1. Dynamically extract identifiers straight from the incoming network air packet
        device_id = discovery_info.upnp.get("serialNumber") or discovery_info.upnp.get("modelNumber")
        device_ip = discovery_info.ssdp_headers.get("_host")
        
        if not device_id or not device_ip:
            return self.async_abort(reason="unknown_device")

        # DHCP TRACKING SHIELD: Update the registry entry automatically if the IP changes
        current_entry = self._async_current_entry()
        if current_entry and current_entry.unique_id == device_id:
            if current_entry.data.get("ip") != device_ip:
                _LOGGER.info("SSDP network update: Device %s moved to new IP %s", device_id, device_ip)
                self.hass.config_entries.async_update_entry(
                    current_entry, 
                    data={**current_entry.data, "ip": device_ip}
                )
            return self.async_abort(reason="already_configured")
                        
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        # 🚀 THE CRITICAL SECURE MEMORY FIX:
        # Save the real dynamic variables straight into the persistent context dictionary layer.
        # This keeps the parameters alive across multi-step UI form wizard confirmation screens.
        self.context["discovery_info"] = {
            "device_id": device_id,
            "ip": device_ip,
            "model_name": discovery_info.upnp.get("modelName") or "FWI",
            "model_number": discovery_info.upnp.get("modelNumber") or "1200"
        }

        self.context["title_placeholders"] = {"name": f"UPSAI ({device_id})"}
        
        # Advance cleanly to the user confirmation step form
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the final user step to confirm setup."""
        # 🚀 EXTRACT RECOVERED VARIABLES FROM CONTEXT MEMORY
        discovery_data = self.context.get("discovery_info", {})
        device_id = discovery_data.get("device_id")
        device_ip = discovery_data.get("ip")
        
        # Throw an alert guard block if a user tries to trigger manual configuration completely blank
        if not device_id or not device_ip:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            model_name = discovery_data.get("model_name") or "FWI"
            model_number = discovery_data.get("model_number") or "1200"
            full_model_string = f"{model_name} {model_number}".strip()

            _LOGGER.info("Successfully committing dynamic entry: ID=%s, IP=%s, Model=%s", device_id, device_ip, full_model_string)

            return self.async_create_entry(
                title=f"UPSAI Remote ({device_id})", 
                data={
                    "device_id": device_id,
                    "ip": device_ip,         # This is now 100% guaranteed to be your dynamic IP!
                    "model": full_model_string
                }
            )
            
        return self.async_show_form(step_id="user")
