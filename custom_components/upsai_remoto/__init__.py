import asyncio
import logging
import json
import aiohttp
import json
import os
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "upsai_remoto"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a pure, event-driven WebSocket pipeline where the hardware dictates the rhythm."""
    
    # 🚀 STRICT DYNAMIC LOOKUP: Strip out the fallback values completely
    device_ip = entry.data.get("ip")
    device_id = entry.data.get("device_id")
    device_model = entry.data.get("model") or "Modelo Indefinido"
    
    # 🚀 DEBUG LOGS: Print the exact variables fetched from the database
    _LOGGER.info(
        "UPSAI Boot Initializer -> Extracted Values from DB: IP=%s, ID=%s, Model=%s",
        device_ip, device_id, device_model
    )
    
    # Validation block: Halt execution immediately if network fields are missing
    if not device_ip or not device_id:
        _LOGGER.error("Fatal initialization error: Dynamic network tracking credentials are missing!")
        return False
        
    # 🎛️ AUTOMATED PLUG & PLAY LOVELACE INJECTION
    try:
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "dashboards.json")
        
        def load_dashboard_file():
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return f.read()
            return None

        # 1. Load your dashboards.json asynchronously
        raw_layout = await hass.async_add_executor_job(load_dashboard_file)

        if raw_layout:
            # 2. Dynamically swap the placeholder with the physical device_id
            processed_layout = raw_layout.replace("TEMPLATE_UNIQUE_ID", str(device_id))
            dashboard_config = json.loads(processed_layout)

            # Establish unique IDs for multi-device support
            dashboard_key = f"upsai_remoto_{entry.entry_id}"
            strategy_name = f"upsai_strategy_{entry.entry_id}"

            # Store the config dict in memory for the strategy to fetch later
            hass.data.setdefault(DOMAIN, {})[f"dash_config_{entry.entry_id}"] = dashboard_config

            # 3. Access the official frontend dashboard registry safely
            frontend = hass.data.get("frontend")
            if frontend and hasattr(frontend, "dashboards"):
                
                # 4. Register the dashboard structure natively in the sidebar array
                frontend.dashboards[dashboard_key] = {
                    "mode": "yaml",
                    "title": "UPSAI Remoto",
                    "icon": "mdi:power-matrix",
                    "show_in_sidebar": True,
                    "require_admin": False,
                    "strategy": {
                        "type": "custom",
                        "name": strategy_name
                    }
                }

                # 5. Define the dynamic layout factory class that Lovelace calls when clicked
                class LovelaceDashboardStrategy:
                    @staticmethod
                    async def async_generate_config(hass_instance, config, *args, **kwargs):
                        # Returns the view layout dictionary directly to the rendering engine
                        return hass_instance.data[DOMAIN].get(f"dash_config_{entry.entry_id}")

                # 6. Register the strategy class into the frontend engine
                if not hasattr(frontend, "dashboard_strategies"):
                    frontend.dashboard_strategies = {}
                frontend.dashboard_strategies[strategy_name] = LovelaceDashboardStrategy

                # 7. Force Home Assistant to instantly draw the new sidebar menu item
                if hasattr(frontend, "async_panels_updated"):
                    frontend.async_panels_updated()

                _LOGGER.info("UPSAI Remoto: Plug & Play dashboard registered successfully.")
            else:
                # Fallback: If frontend is initializing slowly during a cold boot
                _LOGGER.warning("Frontend registry not fully ready yet. Dashboard will retry momentarily.")
        else:
            _LOGGER.error("UPSAI Remoto: Could not find dashboards.json inside the integration folder.")
    except Exception as err:
        _LOGGER.error("UPSAI Remoto: Failed to auto-inject dashboard strategy: %s", err)

    # -------------------
                   
    session = async_get_clientsession(hass)

    class EventDrivenDeviceEngine:
        def __init__(self):
            # Pristine baseline memory state storage
            self.data = {
                "sensors": {"Vin": 0.0, "Vout": 0.0, "Power": 0, "Msg": "Iniciando Canal..."},
                "bank": {"bank0_stat": "00000000", "bank0_lock": "00000000"}
            }
            self.device_ip = device_ip
            self.device_id = device_id
            self.device_model = device_model
            self.listeners = []
            self._ws = None

        def async_add_listener(self, callback):
            """Allows entities (sensors/switches) to bind their redraw hooks."""
            self.listeners.append(callback)

        async def async_send_ws_command(self, command_string: str):
            """Event-Driven Upstream: Fires text commands instantly down the pipe on user click."""
            if self._ws and not self._ws.closed:
                try:
                    _LOGGER.info("Sending Event Upstream: %s", command_string)
                    await self._ws.send_str(command_string)
                except Exception as err:
                    _LOGGER.error("Failed to write to WebSocket stream pipe: %s", err)
            else:
                _LOGGER.warning("Command dropped: Device is currently offline.")

    engine = EventDrivenDeviceEngine()

    async def pure_websocket_listener_task():
        """Asynchronous worker that blocks on incoming network sockets until hardware pushes data."""
        ws_url = f"ws://{device_ip}/websocket"
        
        while True:
            try:
                _LOGGER.info("Opening listener pipe to Mongoose: %s", ws_url)
                async with session.ws_connect(ws_url, heartbeat=10.0) as ws:
                    engine._ws = ws
                    _LOGGER.info("Event-driven pipeline established with Mongoose firmware!")
                    
                    # Fire welcome notification handshake
                    await engine.async_send_ws_command("HA_SYSTEM:CONNECT")
                    
                    # PURE ASYNC STREAM CONSUMPTION:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            parsed_json = json.loads(msg.data)
                            raw_payload = {str(k).strip(): v for k, v in parsed_json.items()}
                            
                            # Parse raw payload parameters directly into memory
                            engine.data = {
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
                            
                            # INSTANT EVENT DISPATCH:
                            for update_callback in engine.listeners:
                                hass.loop.call_soon_threadsafe(update_callback)
                                
            except Exception as err:
                _LOGGER.warning("Connection dropped or unreachable: %s. Re-linking in 5 seconds...", err)
                
                # IMMEDIATE RE-DRAW SIGNAL FOR DISCONNECTION:
                engine._ws = None  # Clear the socket handle first
                for update_callback in engine.listeners:
                    hass.loop.call_soon_threadsafe(update_callback)            
                    
            engine._ws = None
            await asyncio.sleep(5)  # Reconnect cooldown timer window

    # Spin up the background listener task safely in the Home Assistant core pool
    entry.async_create_background_task(hass, pure_websocket_listener_task(), "upsai_ws_listener")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = engine
    
    # Securely registers the dynamic DHCP tracking callback routine using old core naming
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))    

    # Forward the setup configuration straight to your entity platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch", "button"])
    return True

    
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when an automatic network change is detected."""
    _LOGGER.info("Reloading UPSAI Remoto configuration entry due to an IP address update.")
    await hass.config_entries.async_reload(entry.entry_id)    

from homeassistant.components.frontend import async_remove_panel

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload integration entry cleanly and notify the hardware."""
    engine = hass.data[DOMAIN].get(entry.entry_id)
    if engine and engine._ws and not engine._ws.closed:
        try:
            await asyncio.wait_for(engine.async_send_ws_command("HA_SYSTEM:DISCONNECT"), timeout=1.0)
            await engine._ws.close()
        except Exception:
            pass
    # 🎛️ PLUG & PLAY UNLOAD CLEANUP
    try:
        dashboard_key = f"upsai_remoto_{entry.entry_id}"
        strategy_name = f"upsai_strategy_{entry.entry_id}"
        
        frontend = hass.data.get("frontend")
        if frontend:
            if hasattr(frontend, "dashboards"):
                frontend.dashboards.pop(dashboard_key, None)
            if hasattr(frontend, "dashboard_strategies"):
                frontend.dashboard_strategies.pop(strategy_name, None)
            if hasattr(frontend, "async_panels_updated"):
                frontend.async_panels_updated()
                
        hass.data[DOMAIN].pop(f"dash_config_{entry.entry_id}", None)
        _LOGGER.info("UPSAI Remoto: Dashboard successfully removed upon integration unload.")
    except Exception as err:
        _LOGGER.error("UPSAI Remoto: Error during dashboard teardown: %s", err)

    # Continue with your untouched platform unloading sequence
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "button"])
