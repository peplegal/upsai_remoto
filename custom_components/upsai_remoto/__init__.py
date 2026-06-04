from datetime import timedelta
import logging
import json
import asyncio
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UPSAI Remoto over a bulletproof data-injected Coordinator."""
    
    device_ip = entry.data.get("ip") or "192.168.0.3"
    device_id = entry.data.get("device_id") or "P6IO7078YR"
    
    session = async_get_clientsession(hass)

    # Initialize the official HA Coordinator with NO polling interval (None)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"UPSAI WS Coordinator ({device_id})",
        update_interval=None, # Disables HTTP polling entirely
    )

    # Inject dynamic device identifiers onto the coordinator object canvas
    coordinator.device_ip = device_ip
    coordinator.device_id = device_id
    coordinator._ws = None  # Live socket tracking pointer

    async def async_send_ws_command(command_string: str):
        """Pushes pure command strings directly back down the active pipe."""
        if coordinator._ws and not coordinator._ws.closed:
            try:
                _LOGGER.info("Sending WS Command: %s", command_string)
                await coordinator._ws.send_str(command_string)
            except Exception as err:
                _LOGGER.error("Failed to write to WebSocket stream pipe: %s", err)
        else:
            _LOGGER.warning("Command dropped: WebSocket connection is offline.")

    # Bind the sender function directly to the coordinator object asset
    coordinator.async_send_ws_command = async_send_ws_command

    async def websocket_listener_task():
        """Maintains the background connection and safely feeds the native cache."""
        ws_url = f"ws://{device_ip}/websocket"
        
        # INFINITE NETWORK DAEMON LOOP: This task will run for as long as HA is booted
        while True:
            try:
                _LOGGER.info("Attempting connection to bidirectional Mongoose WebSocket: %s", ws_url)
                
                # We add a 4-second timeout to the connect step itself so a dead route can't freeze the script
                async with async_timeout.timeout(4.0) if "async_timeout" in globals() else asyncio.timeout(4.0):
                    async with session.ws_connect(ws_url, heartbeat=10.0) as ws:
                        coordinator._ws = ws
                        _LOGGER.info("Bidirectional string pipeline established with Mongoose firmware!")
                        
                        # Fire welcome packet sequence 
                        await coordinator.async_send_ws_command("HA_SYSTEM:CONNECT")
                        
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                parsed_json = json.loads(msg.data)
                                
                                # Clean up and sanitize incoming keys dynamically
                                raw_payload = {str(k).strip(): v for k, v in parsed_json.items()}
                                
                                # Build the exact data structure your entities expect
                                new_data = {
                                    "sensors": {
                                        "Vin": float(raw_payload.get("Vin", 0.0)),
                                        "Vout": float(raw_payload.get("Vout", 0.0)),
                                        "Power": int(raw_payload.get("Power", 0)),
                                        "Msg": str(raw_payload.get("Msg", "WS Telemetry Active")).strip()
                                    },
                                    "bank": {
                                        "bank0_stat": str(raw_payload.get("bank0_stat", "00000000")).strip(),
                                        "bank0_lock": str(raw_payload.get("bank0_lock", "00000000")).strip()
                                    }
                                }
                                
                                # Safely updates the core cache and pushes to UI inside the main thread loop
                                hass.loop.call_soon_threadsafe(coordinator.async_set_updated_data, new_data)
                                    
            # 🚀 BULLETPROOF CATCH-ALL: Intercepts all timeout, host unreachable, and socket drops cleanly
            except Exception as err:
                _LOGGER.warning("UPSAI device connection dropped or unreachable: %s. Re-trying in 5 seconds...", err)
            
            # Reset the socket assignment pointer so commands know the channel is down
            coordinator._ws = None
            
            # Enforce a flat 5-second rest window before trying the network connection loop again
            await asyncio.sleep(5)

    # Launch background task safely inside the container daemon pool
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