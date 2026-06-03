import asyncio
import logging
import json
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UPSAI Remoto over a persistent bidirectional WebSocket connection."""
    
    device_ip = entry.data.get("ip") or "192.168.0.3"
    device_id = entry.data.get("device_id") or "P6IO7078YR"
    
    session = async_get_clientsession(hass)

    # Core system runtime state container registry mimic
    class WebSocketCoordinator:
        def __init__(self):
            self.data = {"sensors": {}, "bank": {}}
            self.device_ip = device_ip
            self.device_id = device_id
            self.listeners = []
            self._ws = None  # Holds the live active socket connection object pointer

        def async_add_listener(self, callback):
            """Allows entities to bind UI refresh actions."""
            self.listeners.append(callback)

        async def async_send_ws_command(self, command_string: str):
            """Pushes pure command strings directly back down the active pipe."""
            if self._ws and not self._ws.closed:
                try:
                    _LOGGER.info("Sending WS Command: %s", command_string)
                    # Sends plain text directly to your Mongoose websocket_handler
                    await self._ws.send_str(command_string)
                except Exception as err:
                    _LOGGER.error("Failed to write to WebSocket stream pipe: %s", err)
            else:
                _LOGGER.warning("Command dropped: WebSocket connection is offline.")

    coordinator = WebSocketCoordinator()

    async def websocket_listener_task():
        """Maintains connection to Mongoose default /websocket route endpoint."""
        ws_url = f"ws://{device_ip}/websocket"
        
        while True:
            try:
                _LOGGER.info("Connecting to bidirectional Mongoose WebSocket: %s", ws_url)
                async with session.ws_connect(ws_url, heartbeat=10.0) as ws:
                    coordinator._ws = ws  # Map the socket reference to our coordinator
                    _LOGGER.info("Bidirectional string pipeline established with Mongoose firmware!")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            raw_payload = json.loads(msg.data)
                            
                            # Standardize layout parameters mapping from your compressed payload format
                            coordinator.data = {
                                "sensors": {
                                    "Vin": raw_payload.get("Vin", 0.0),
                                    "Vout": raw_payload.get("Vout", 0.0),
                                    "Power": raw_payload.get("Power", 0),
                                    "Msg": raw_payload.get("Msg", "WS Telemetry Active")
                                },
                                "bank": {
                                    "bank0_stat": raw_payload.get("bank0_stat", "00000000"),
                                    "bank0_lock": raw_payload.get("bank0_lock", "00000000")
                                }
                            }
                            
                            # Instant UI redraw prompt trigger
                            for update_callback in coordinator.listeners:
                                update_callback()
                                
            except aiohttp.ClientError as err:
                _LOGGER.warning("Mongoose stream dropped: %s. Re-linking in 5s...", err)
            except Exception as err:
                _LOGGER.error("WebSocket background task exception error: %s", err)
            
            coordinator._ws = None  # Clear socket layout assignment on break
            await asyncio.sleep(5)

    # Launch background thread daemon loop pool controller task worker
    entry.async_create_background_task(hass, websocket_listener_task(), "upsai_ws_listener")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry data paths cleanly from backend loops."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "button"])
