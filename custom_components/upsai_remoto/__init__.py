import asyncio
import logging
import re
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UPSAI Remoto over a persistent raw-string parsing WebSocket connection."""
    
    device_ip = entry.data.get("ip") or "192.168.0.3"
    device_id = entry.data.get("device_id") or "P6IO7078YR"
    
    session = async_get_clientsession(hass)

    class WebSocketCoordinator:
        def __init__(self):
            self.data = {"sensors": {}, "bank": {}}
            self.device_ip = device_ip
            self.device_id = device_id
            self.listeners = []
            self._ws = None

        def async_add_listener(self, callback):
            self.listeners.append(callback)

        async def async_send_ws_command(self, command_string: str):
            """Pushes pure command strings directly back down the active pipe."""
            if self._ws and not self._ws.closed:
                try:
                    _LOGGER.info("Sending WS Command: %s", command_string)
                    await self._ws.send_str(command_string)
                except Exception as err:
                    _LOGGER.error("Failed to write to WebSocket stream pipe: %s", err)
            else:
                _LOGGER.warning("Command dropped: WebSocket connection is offline.")

    coordinator = WebSocketCoordinator()

    async def websocket_listener_task():
        """Maintains connection and extracts data using raw string matching."""
        ws_url = f"ws://{device_ip}/websocket"
        
        while True:
            try:
                _LOGGER.info("Connecting to bidirectional Mongoose WebSocket: %s", ws_url)
                async with session.ws_connect(ws_url, heartbeat=5.0) as ws:
                    coordinator._ws = ws
                    _LOGGER.info("Bidirectional string pipeline established with Mongoose firmware!")
                    
                    # Fire welcome packet sequence 
                    await coordinator.async_send_ws_command("HA_SYSTEM:CONNECT")
                    
                    async for msg in ws:
                        if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                            raw_text = str(msg.data)
                            
                            # 🚀 FIXED REGEX LAYER: Clean extraction of numeric and bitmask elements
                            vin_match = re.search(r'"Vin"\s*:\s*([\d.]+)', raw_text)
                            vout_match = re.search(r'"Vout"\s*:\s*([\d.]+)', raw_text)
                            power_match = re.search(r'"Power"\s*:\s*(\d+)', raw_text)
                            msg_match = re.search(r'"Msg"\s*:\s*"([^"]+)"', raw_text)
                            
                            # Specifically extracts exactly 8 occurrences of characters 0 or 1
                            stat_match = re.search(r'"bank0_stat"\s*:\s*"([01]{8})"', raw_text)
                            lock_match = re.search(r'"bank0_lock"\s*:\s*"([01]{8})"', raw_text)
                            
                            coordinator.data = {
                                "sensors": {
                                    "Vin": float(vin_match.group(1)) if vin_match else 0.0,
                                    "Vout": float(vout_match.group(1)) if vout_match else 0.0,
                                    "Power": int(power_match.group(1)) if power_match else 0,
                                    "Msg": msg_match.group(1) if msg_match else "WS Telemetry Active"
                                },
                                "bank": {
                                    "bank0_stat": stat_match.group(1) if stat_match else "00000000",
                                    "bank0_lock": lock_match.group(1) if lock_match else "00000000"
                                }
                            }
                            
                            # Execute immediate interface updates across all registered objects
                            for update_callback in coordinator.listeners:
                                update_callback()
                                
            except Exception as err:
                _LOGGER.warning("Mongoose stream closed or dropped: %s. Re-linking in 5s...", err)
            
            coordinator._ws = None
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, websocket_listener_task(), "upsai_ws_listener")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry data paths cleanly and send a Goodbye notification."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        try:
            await asyncio.wait_for(coordinator.async_send_ws_command("HA_SYSTEM:DISCONNECT"), timeout=1.0)
        except Exception:
            pass
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "button"])
