"""Canaan Avalon Miner DataUpdateCoordinator."""
import asyncio
import logging
import re
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    LED_EFFECT_MAP,
    LEVEL_MAP_MINI3,
    MODE_MAP_MINI3,
    MODE_MAP_NANO3S,
    MODE_MAP_Q,
    MODEL_MINI3,
    MODEL_NAMES,
    MODEL_NANO3S,
    MODEL_Q,
    MODEL_UNKNOWN,
    STATE_MAP,
    WORK_LEVEL_ECO_MINI3,
    WORK_LEVEL_SUPER_MINI3,
    WORK_MODE_HEATING,
    WORK_MODE_MINING,
    WORK_MODE_NIGHT,
)

_LOGGER = logging.getLogger(__name__)

# Default data structure for Mini 3
DEFAULT_DATA_MINI3 = {
    "hostname": None,
    "mac": None,
    "make": "Canaan",
    "model": "Avalon Mini 3",
    "model_type": MODEL_MINI3,
    "ip": None,
    "hashrate": 0.0,
    "internal_temp": 0,
    "output_temp": 0,
    "hb_temp": 0,
    "max_temp": 0,
    "avg_temp": 0,
    "target_temp": 0,
    "fan_rpm": 0,
    "fan_percentage": 0,
    "power": 0,
    "state": "Unknown",
    "mode": "Unknown",
    "level": "Unknown",
    "state_num": 0,
    "mode_num": 0,
    "level_num": 0,
    "soft_off": 0,
    "elapsed": 0,
    "serial": None,
    "firmware": None,
}

# Default data structure for Avalon Q
DEFAULT_DATA_Q = {
    "hostname": None,
    "mac": None,
    "make": "Canaan",
    "model": "Avalon Q",
    "model_type": MODEL_Q,
    "ip": None,
    "hashrate": 0.0,
    "internal_temp": 0,
    "hb_internal_temp": 0,
    "hb_output_temp": 0,
    "output_temp": 0,
    "max_temp": 0,
    "avg_temp": 0,
    "target_temp": 0,
    "fan_percentage": 0,
    "wifi_rssi": 0,
    "power": 0,
    "state": "Unknown",
    "mode": "Unknown",
    "level": "Unknown",
    "state_num": 0,
    "mode_num": 0,
    "level_num": 0,
    "soft_off": 0,
    "elapsed": 0,
    "serial": None,
    "firmware": None,
}

# Default data structure for Nano 3s
DEFAULT_DATA_NANO3S = {
    "hostname": None,
    "mac": None,
    "make": "Canaan",
    "model": "Avalon Nano 3s",
    "model_type": MODEL_NANO3S,
    "ip": None,
    "hashrate": 0.0,
    "internal_temp": 0,
    "output_temp": 0,
    "max_temp": 0,
    "avg_temp": 0,
    "target_temp": 0,
    "fan_rpm": 0,
    "fan_percentage": 0,
    "power": 0,
    "state": "Unknown",
    "mode": "Unknown",
    "state_num": 0,
    "mode_num": 0,
    "soft_off": 0,
    "elapsed": 0,
    "serial": None,
    "firmware": None,
    # LED settings
    "led_effect": 0,
    "led_effect_name": "Off",
    "led_brightness": 0,
    "led_color_temp": 0,
    "led_r": 0,
    "led_g": 0,
    "led_b": 0,
    "led_on": False,
}

# Legacy alias
DEFAULT_DATA = DEFAULT_DATA_MINI3


async def scan_for_miners(
    network_prefix: str,
    port: int = 4028,
    timeout: float = 1.0,
    max_concurrent: int = 50,
) -> list[dict]:
    """Scan a network subnet for Canaan Avalon miners.
    
    Args:
        network_prefix: The network prefix (e.g., "192.168.1")
        port: The port to scan (default 4028 for CGMiner API)
        timeout: Connection timeout per host in seconds
        max_concurrent: Maximum concurrent connection attempts
    
    Returns:
        List of dicts with keys: ip, model_type, model_name
    """
    discovered = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_host(ip: str) -> dict | None:
        """Check if a host is a Canaan miner."""
        async with semaphore:
            try:
                # Try to connect to the port
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                # Port is open, try to detect model
                model_type, model_name = await detect_model(ip, port)
                
                if model_type != MODEL_UNKNOWN:
                    _LOGGER.info(f"Discovered {model_name} at {ip}")
                    return {
                        "ip": ip,
                        "model_type": model_type,
                        "model_name": model_name,
                    }
                else:
                    # Port open but not a recognized Canaan/Avalon miner - skip it
                    _LOGGER.debug(f"Port {port} open at {ip} but not a recognized Avalon miner, skipping")
                    return None
                    
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                # Host not responding or port closed
                return None
            except Exception as err:
                _LOGGER.debug(f"Error checking {ip}: {err}")
                return None
    
    # Generate IP addresses for the subnet (1-254)
    ips = [f"{network_prefix}.{i}" for i in range(1, 255)]
    
    # Scan all IPs concurrently
    _LOGGER.info(f"Scanning {network_prefix}.0/24 for Canaan miners on port {port}...")
    tasks = [check_host(ip) for ip in ips]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results
    discovered = [r for r in results if r is not None]
    
    _LOGGER.info(f"Scan complete. Found {len(discovered)} miner(s)")
    return discovered


def get_network_prefixes_from_ip(ip_address: str) -> list[str]:
    """Extract network prefix from an IP address (assumes /24 subnet).
    
    Args:
        ip_address: An IP address like "192.168.1.100"
    
    Returns:
        List containing the network prefix like ["192.168.1"]
    """
    parts = ip_address.split(".")
    if len(parts) == 4:
        return [".".join(parts[:3])]
    return []


class CanaanAPI:
    """Direct API communication with Canaan Avalon miners via TCP.
    
    Supports both Mini 3/Q (JSON format) and Nano 3s (plain text CGMiner format).
    """

    def __init__(self, host: str, port: int, model_type: str = MODEL_UNKNOWN):
        """Initialize API."""
        self.host = host
        self.port = port
        self.model_type = model_type

    async def _send_tcp(self, message: str, timeout: int = 5) -> str | None:
        """Send raw TCP message and get response."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout
            )
            
            _LOGGER.debug(f"Sending to {self.host}: {message}")
            
            writer.write(message.encode('utf-8'))
            await writer.drain()
            
            # Read response - Nano 3s can return larger responses
            data = await asyncio.wait_for(reader.read(16384), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            
            if not data:
                _LOGGER.warning(f"Empty response from {self.host}")
                return None
            
            response_str = data.decode('utf-8', errors='ignore').strip()
            _LOGGER.debug(f"Received from {self.host}: {response_str[:500]}")
            
            return response_str
            
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout connecting to {self.host}:{self.port}")
            return None
        except ConnectionRefusedError:
            _LOGGER.error(f"Connection refused to {self.host}:{self.port}")
            return None
        except Exception as err:
            _LOGGER.exception(f"Error communicating with {self.host}: {err}")
            return None

    async def send_command(self, command: str, timeout: int = 5) -> str | None:
        """Send command to miner and get response.
        
        For Mini 3/Q: Uses JSON format {"command":"..."}
        For Nano 3s: Uses plain text format
        """
        if self.model_type == MODEL_NANO3S:
            # Nano 3s uses plain text commands
            return await self._send_tcp(command, timeout)
        else:
            # Mini 3/Q uses JSON format
            message = f'{{"command":"{command}"}}'
            return await self._send_tcp(message, timeout)

    async def send_raw_command(self, command: str, timeout: int = 5) -> str | None:
        """Send raw command to miner (for ascset commands - works on all models)."""
        return await self._send_tcp(command, timeout)

    async def get_version(self) -> str | None:
        """Get version info (used for model detection)."""
        return await self._send_tcp("version", timeout=5)

    async def get_stats(self) -> str | None:
        """Get miner statistics."""
        # All models use plain text estats command for full stats including power
        return await self._send_tcp("estats", timeout=5)

    async def set_work_mode(self, mode: int) -> bool:
        """Set work mode.
        
        Mini 3/Q: 0=heating, 1=mining, 2=night
        Nano 3s: 0=low, 1=mid, 2=high
        """
        try:
            command = f"ascset|0,workmode,set,{mode}"
            response = await self.send_raw_command(command)
            return response is not None and "STATUS=S" in response if self.model_type == MODEL_NANO3S else response is not None
        except Exception as err:
            _LOGGER.error(f"Failed to set work mode: {err}")
            return False

    async def set_work_level(self, level: int) -> bool:
        """Set work level (0=super, -1=eco). Mini 3/Q only."""
        if self.model_type == MODEL_NANO3S:
            _LOGGER.warning("Work level is not supported on Nano 3s")
            return False
        try:
            command = f"ascset|0,worklevel,set,{level}"
            response = await self.send_raw_command(command)
            return response is not None
        except Exception as err:
            _LOGGER.error(f"Failed to set work level: {err}")
            return False

    async def turn_on(self) -> bool:
        """Turn on the miner."""
        try:
            timestamp = int(time.time()) + 5
            command = f"ascset|0,softon,1:{timestamp}"
            response = await self.send_raw_command(command)
            return response is not None
        except Exception as err:
            _LOGGER.error(f"Failed to turn on miner: {err}")
            return False

    async def turn_off(self) -> bool:
        """Turn off the miner."""
        try:
            timestamp = int(time.time()) + 5
            command = f"ascset|0,softoff,1:{timestamp}"
            response = await self.send_raw_command(command)
            return response is not None
        except Exception as err:
            _LOGGER.error(f"Failed to turn off miner: {err}")
            return False

    async def reboot(self) -> bool:
        """Reboot the miner."""
        try:
            command = "ascset|0,reboot,0"
            response = await self.send_raw_command(command)
            return response is not None
        except Exception as err:
            _LOGGER.error(f"Failed to reboot miner: {err}")
            return False

    async def set_led(
        self,
        effect: int = 1,
        brightness: int = 100,
        color_temp: int = 100,
        r: int = 255,
        g: int = 255,
        b: int = 255,
    ) -> bool:
        """Set LED settings (Nano 3s only).
        
        Args:
            effect: 0=off, 1=on, 2=flash, 3=breath, 4=loop
            brightness: 0-100
            color_temp: 0-100
            r, g, b: 0-255
        """
        if self.model_type != MODEL_NANO3S:
            _LOGGER.warning("LED control is only supported on Nano 3s")
            return False
        try:
            command = f"ascset|0,ledset,{effect}-{brightness}-{color_temp}-{r}-{g}-{b}"
            response = await self.send_raw_command(command)
            return response is not None and "led set ok" in response.lower()
        except Exception as err:
            _LOGGER.error(f"Failed to set LED: {err}")
            return False


async def detect_model(host: str, port: int) -> tuple[str, str]:
    """Detect the miner model by querying the version endpoint.
    
    Returns:
        Tuple of (model_type, model_name)
    """
    api = CanaanAPI(host, port, MODEL_UNKNOWN)
    
    # Try version command first
    response = await api.get_version()
    
    if response:
        _LOGGER.debug(f"Version response from {host}: {response[:200]}")
        
        # Check for Nano 3s
        if "PROD=Avalon Nano3s" in response or "Nano3s" in response:
            _LOGGER.info(f"Detected Avalon Nano 3s at {host} via version command")
            return MODEL_NANO3S, "Avalon Nano 3s"
        
        # Check for Q - be more thorough
        if "PROD=Avalon Q" in response or "MODEL=Q" in response or "HWTYPE=Q_" in response:
            _LOGGER.info(f"Detected Avalon Q at {host} via version command")
            return MODEL_Q, "Avalon Q"
        
        # Check for Mini 3
        if "PROD=Avalon Mini" in response or "Mini3" in response:
            _LOGGER.info(f"Detected Avalon Mini 3 at {host} via version command")
            return MODEL_MINI3, "Avalon Mini 3"
        
        # Check for other models in version response
        if "PROD=" in response:
            match = re.search(r'PROD=([^,|]+)', response)
            if match:
                prod = match.group(1).strip()
                if "Mini" in prod:
                    _LOGGER.info(f"Detected {prod} at {host} via PROD field")
                    return MODEL_MINI3, prod
                elif "Q" in prod:
                    _LOGGER.info(f"Detected {prod} at {host} via PROD field")
                    return MODEL_Q, prod
                elif "Nano" in prod:
                    _LOGGER.info(f"Detected {prod} at {host} via PROD field")
                    return MODEL_NANO3S, prod
    
    # Try estats command (all models support this)
    response = await api._send_tcp("estats", timeout=5)
    if response:
        _LOGGER.debug(f"Estats response from {host}: {response[:200]}")
        
        # Check for Q signature in response - be thorough
        if "Ver[Q-" in response or "CPU[K230]" in response or "HWTYPE=Q_" in response:
            _LOGGER.info(f"Detected Avalon Q at {host} via estats command")
            return MODEL_Q, "Avalon Q"
        # Check for Nano 3s signature
        if "Ver[Nano3s-" in response:
            _LOGGER.info(f"Detected Avalon Nano 3s at {host} via estats command")
            return MODEL_NANO3S, "Avalon Nano 3s"
        # Check for Mini 3 signature
        if "Ver[Mini3-" in response:
            _LOGGER.info(f"Detected Avalon Mini 3 at {host} via estats command")
            return MODEL_MINI3, "Avalon Mini 3"
        # Generic fallback - only if we have a miner response but can't identify it
        if "GHSspd[" in response:
            _LOGGER.warning(
                f"Detected unknown Avalon miner at {host} via estats, "
                f"defaulting to Mini 3. Please report this detection issue."
            )
            return MODEL_MINI3, "Avalon Mini 3"
    
    _LOGGER.warning(f"Could not detect model at {host}, no valid response received")
    return MODEL_UNKNOWN, "Avalon Miner"


class CanaanCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Canaan Avalon Miner data."""

    def __init__(
        self,
        hass: HomeAssistant,
        ip: str,
        port: int,
        scan_interval: int,
        name: str,
        model_type: str = MODEL_UNKNOWN,
        model_name: str = "Avalon Miner",
    ) -> None:
        """Initialize coordinator."""
        self.miner_ip = ip
        self.port = port
        self.model_type = model_type
        self.model_name = model_name
        self.api = CanaanAPI(ip, port, model_type)
        self._failure_count = 0
        
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _parse_stats_mini3(self, response: str) -> dict:
        """Parse estats response for Mini 3.
        
        Response format example (CGMiner format):
        ...MM ID0=HashStatus[0] Ver[Mini3-...] ... PS[0 1218 2091 36 755 2090 839] ...
        """
        # Start with previous data if available, otherwise use defaults
        # This preserves values that might not be in every response
        if hasattr(self, 'data') and self.data:
            data = self.data.copy()
        else:
            data = DEFAULT_DATA_MINI3.copy()
        
        data["ip"] = self.miner_ip
        data["mac"] = f"canaan_{self.miner_ip.replace('.', '_')}"
        data["model"] = self.model_name
        data["model_type"] = self.model_type
        
        try:
            # Extract hashrate (GHSspd) - convert GH/s to TH/s
            match = re.search(r'GHSspd\[([\d.]+)\]', response)
            if match:
                data["hashrate"] = round(float(match.group(1)) / 1000, 2)
            
            # Extract internal/ambient temperature
            match = re.search(r'ITemp\[(-?\d+)\]', response)
            if match:
                temp = int(match.group(1))
                data["internal_temp"] = temp if temp > -200 else 0
            
            # Extract output temperature
            match = re.search(r'OTemp\[(\d+)\]', response)
            if match:
                data["output_temp"] = int(match.group(1))
            
            # Extract hash board temperature
            match = re.search(r'HBTemp\[(\d+)\]', response)
            if match:
                data["hb_temp"] = int(match.group(1))
            
            # Extract max temperature
            match = re.search(r'TMax\[(\d+)\]', response)
            if match:
                data["max_temp"] = int(match.group(1))
            
            # Extract average temperature
            match = re.search(r'TAvg\[(\d+)\]', response)
            if match:
                data["avg_temp"] = int(match.group(1))
            
            # Extract target temperature
            match = re.search(r'TarT\[(\d+)\]', response)
            if match:
                data["target_temp"] = int(match.group(1))
            
            # Extract fan RPM
            match = re.search(r'Fan1\[(\d+)\]', response)
            if match:
                data["fan_rpm"] = int(match.group(1))
            
            # Extract fan percentage
            match = re.search(r'FanR\[(\d+)%?\]', response)
            if match:
                data["fan_percentage"] = int(match.group(1))
            
            # Extract power consumption from PS array (last value is watts)
            match = re.search(r'PS\[[\d\s]+\s(\d+)\]', response)
            if match:
                data["power"] = int(match.group(1))
            
            # Extract soft off state
            match = re.search(r'SoftOFF\[(\d+)\]', response)
            if match:
                data["soft_off"] = int(match.group(1))
            
            # Determine state from SYSTEMSTATU field
            if "Work: In Work" in response:
                data["state_num"] = 1
                data["state"] = "Working"
            elif "Work: In Idle" in response or "Work: Idle" in response or "Work: Off" in response:
                data["state_num"] = 2
                data["state"] = "Idle"
            else:
                # Fallback: check if hashrate > 0
                if data.get("hashrate", 0) > 0:
                    data["state_num"] = 1
                    data["state"] = "Working"
                else:
                    data["state_num"] = 2
                    data["state"] = "Idle"
            
            # Extract work mode
            match = re.search(r'WORKMODE\[(\d+)\]', response)
            if match:
                mode_num = int(match.group(1))
                data["mode_num"] = mode_num
                data["mode"] = MODE_MAP_MINI3.get(mode_num, "Unknown")
            else:
                _LOGGER.debug(f"WORKMODE not found in Mini 3 response from {self.miner_ip}, preserving previous value: {data.get('mode')}")
            
            # Extract work level
            match = re.search(r'WORKLEVEL\[(-?\d+)\]', response)
            if match:
                level_num = int(match.group(1))
                data["level_num"] = level_num
                data["level"] = LEVEL_MAP_MINI3.get(level_num, "Unknown")
            else:
                _LOGGER.debug(f"WORKLEVEL not found in Mini 3 response from {self.miner_ip}, preserving previous value: {data.get('level')}")
            
            # Extract elapsed time (uptime)
            match = re.search(r'Elapsed\[(\d+)\]', response)
            if match:
                data["elapsed"] = int(match.group(1))
            
            # Extract DNA (serial number)
            match = re.search(r'DNA\[([^\]]+)\]', response)
            if match:
                data["serial"] = match.group(1)
                # Use DNA as unique identifier for mac
                data["mac"] = f"canaan_{match.group(1)}"
            
            # Extract firmware version
            match = re.search(r'Ver\[([^\]]+)\]', response)
            if match:
                data["firmware"] = match.group(1)
            
        except Exception as err:
            _LOGGER.error(f"Error parsing Mini 3 stats: {err}")
        
        return data

    def _parse_stats_nano3s(self, response: str) -> dict:
        """Parse estats response for Nano 3s.
        
        Response format example (CGMiner format):
        STATUS=S,When=...|STATS=0,ID=AVALON0,...MM ID0=Ver[...] ... GHSspd[3129.79] ...
        """
        # Start with previous data if available, otherwise use defaults
        # This preserves values that might not be in every response
        if hasattr(self, 'data') and self.data:
            data = self.data.copy()
        else:
            data = DEFAULT_DATA_NANO3S.copy()
        
        data["ip"] = self.miner_ip
        data["mac"] = f"canaan_{self.miner_ip.replace('.', '_')}"
        data["model"] = self.model_name
        data["model_type"] = self.model_type
        
        try:
            # Extract hashrate (GHSspd) - convert GH/s to TH/s
            match = re.search(r'GHSspd\[([\d.]+)\]', response)
            if match:
                data["hashrate"] = round(float(match.group(1)) / 1000, 2)
            
            # Extract internal temperature (may be -273 if no sensor)
            match = re.search(r'ITemp\[(-?\d+)\]', response)
            if match:
                temp = int(match.group(1))
                data["internal_temp"] = temp if temp > -200 else 0
            
            # Extract output temperature
            match = re.search(r'OTemp\[(\d+)\]', response)
            if match:
                data["output_temp"] = int(match.group(1))
            
            # Extract max temperature
            match = re.search(r'TMax\[(\d+)\]', response)
            if match:
                data["max_temp"] = int(match.group(1))
            
            # Extract average temperature
            match = re.search(r'TAvg\[(\d+)\]', response)
            if match:
                data["avg_temp"] = int(match.group(1))
            
            # Extract target temperature
            match = re.search(r'TarT\[(\d+)\]', response)
            if match:
                data["target_temp"] = int(match.group(1))
            
            # Extract fan RPM
            match = re.search(r'Fan1\[(\d+)\]', response)
            if match:
                data["fan_rpm"] = int(match.group(1))
            
            # Extract fan percentage
            match = re.search(r'FanR\[(\d+)%?\]', response)
            if match:
                data["fan_percentage"] = int(match.group(1))
            
            # Extract power consumption from PS array (index 6 is watts)
            # PS format: PS[0 0 voltage 3 0 value watts]
            match = re.search(r'PS\[[\d\s]+\s(\d+)\]', response)
            if match:
                data["power"] = int(match.group(1))
            
            # Extract work mode
            match = re.search(r'WORKMODE\[(\d+)\]', response)
            if match:
                mode_num = int(match.group(1))
                data["mode_num"] = mode_num
                data["mode"] = MODE_MAP_NANO3S.get(mode_num, "Unknown")
            else:
                _LOGGER.debug(f"WORKMODE not found in Nano 3s response from {self.miner_ip}, preserving previous value: {data.get('mode')}")
            
            # Extract soft off state
            match = re.search(r'SoftOFF\[(\d+)\]', response)
            if match:
                data["soft_off"] = int(match.group(1))
            
            # Determine state from SYSTEMSTATU field
            if "Work: In Work" in response:
                data["state_num"] = 1
                data["state"] = "Working"
            elif "Work: In Idle" in response or "Work: Idle" in response or "Work: Off" in response:
                data["state_num"] = 2
                data["state"] = "Idle"
            else:
                # Fallback: check if hashrate > 0
                if data.get("hashrate", 0) > 0:
                    data["state_num"] = 1
                    data["state"] = "Working"
                else:
                    data["state_num"] = 2
                    data["state"] = "Idle"
            
            # Extract elapsed time (uptime)
            match = re.search(r'Elapsed\[(\d+)\]', response)
            if match:
                data["elapsed"] = int(match.group(1))
            
            # Extract DNA (serial number)
            match = re.search(r'DNA\[([^\]]+)\]', response)
            if match:
                data["serial"] = match.group(1)
                # Use DNA as unique identifier for mac
                data["mac"] = f"canaan_{match.group(1)}"
            
            # Extract firmware version
            match = re.search(r'Ver\[([^\]]+)\]', response)
            if match:
                data["firmware"] = match.group(1)
            
            # Extract LED settings: LED[effect-state] LEDUser[effect-bright-temp-r-g-b]
            match = re.search(r'LED\[(\d+)-(\d+)\]', response)
            if match:
                data["led_effect"] = int(match.group(1))
                data["led_on"] = int(match.group(2)) == 1
            
            match = re.search(r'LEDUser\[(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)\]', response)
            if match:
                data["led_effect"] = int(match.group(1))
                data["led_effect_name"] = LED_EFFECT_MAP.get(int(match.group(1)), "Unknown")
                data["led_brightness"] = int(match.group(2))
                data["led_color_temp"] = int(match.group(3))
                data["led_r"] = int(match.group(4))
                data["led_g"] = int(match.group(5))
                data["led_b"] = int(match.group(6))
                # LED is "on" if effect > 0 (not "off")
                data["led_on"] = int(match.group(1)) > 0
            
        except Exception as err:
            _LOGGER.error(f"Error parsing Nano 3s stats: {err}")
        
        return data

    def _parse_stats_q(self, response: str) -> dict:
        """Parse estats response for Avalon Q.
        
        Response format example (CGMiner format with nested structure):
        ...MM ID0:Summary='STATS':{Ver[Q-...] ... PS[0 1217 2396 54 1305 2397 1417] ...}...
        
        Note: Q uses WORKMODE field for performance levels (Eco/Standard/Super),
        not for heating modes like Mini 3. WORKLEVEL field is ignored.
        """
        # Start with previous data if available, otherwise use defaults
        # This preserves values that might not be in every response
        if hasattr(self, 'data') and self.data:
            data = self.data.copy()
        else:
            data = DEFAULT_DATA_Q.copy()
        
        data["ip"] = self.miner_ip
        data["mac"] = f"canaan_{self.miner_ip.replace('.', '_')}"
        data["model"] = self.model_name
        data["model_type"] = self.model_type
        
        try:
            # Extract hashrate (GHSspd) - convert GH/s to TH/s
            match = re.search(r'GHSspd\[([\d.]+)\]', response)
            if match:
                data["hashrate"] = round(float(match.group(1)) / 1000, 2)
            
            # Extract internal temperature (ambient)
            match = re.search(r'ITemp\[(-?\d+)\]', response)
            if match:
                temp = int(match.group(1))
                data["internal_temp"] = temp if temp > -200 else 0
            
            # Extract hash board internal temperature
            match = re.search(r'HBITemp\[(\d+)\]', response)
            if match:
                data["hb_internal_temp"] = int(match.group(1))
            
            # Extract hash board output temperature
            match = re.search(r'HBOTemp\[(\d+)\]', response)
            if match:
                data["hb_output_temp"] = int(match.group(1))
                data["output_temp"] = int(match.group(1))  # Use as primary output temp
            
            # Extract max temperature
            match = re.search(r'TMax\[(\d+)\]', response)
            if match:
                data["max_temp"] = int(match.group(1))
            
            # Extract average temperature
            match = re.search(r'TAvg\[(\d+)\]', response)
            if match:
                data["avg_temp"] = int(match.group(1))
            
            # Extract target temperature
            match = re.search(r'TarT\[(\d+)\]', response)
            if match:
                data["target_temp"] = int(match.group(1))
            
            # Extract fan percentage
            match = re.search(r'FanR\[(\d+)%?\]', response)
            if match:
                data["fan_percentage"] = int(match.group(1))
            
            # Extract WiFi RSSI
            match = re.search(r'RSSI\[(-?\d+)\]', response)
            if match:
                data["wifi_rssi"] = int(match.group(1))
            
            # Extract power consumption from PS array (index 6 is watts)
            # PS format: PS[0 1217 2396 54 1305 2397 1417]
            match = re.search(r'PS\[[\d\s]+\s(\d+)\]', response)
            if match:
                data["power"] = int(match.group(1))
            
            # Extract soft off state
            match = re.search(r'SoftOFF\[(\d+)\]', response)
            if match:
                data["soft_off"] = int(match.group(1))
            
            # Determine state - first try STATE field, then SYSTEMSTATU
            match = re.search(r'STATE\[(\d+)\]', response)
            if match:
                state_num = int(match.group(1))
                data["state_num"] = state_num
                data["state"] = STATE_MAP.get(state_num, "Unknown")
            elif "Work: In Work" in response:
                data["state_num"] = 1
                data["state"] = "Working"
            elif "Work: In Idle" in response or "Work: Idle" in response or "Work: Off" in response:
                data["state_num"] = 2
                data["state"] = "Idle"
            else:
                # Fallback: check if hashrate > 0
                if data.get("hashrate", 0) > 0:
                    data["state_num"] = 1
                    data["state"] = "Working"
                else:
                    data["state_num"] = 2
                    data["state"] = "Idle"
            
            # For Avalon Q: WORKMODE field contains performance level (0=Eco, 1=Standard, 2=Super)
            # This is different from Mini 3 where WORKMODE is heating/mining/night
            match = re.search(r'WORKMODE\[(\d+)\]', response)
            if match:
                level_num = int(match.group(1))
                data["level_num"] = level_num
                data["level"] = MODE_MAP_Q.get(level_num, "Unknown")
                # Also store in mode for backwards compatibility
                data["mode_num"] = level_num
                data["mode"] = MODE_MAP_Q.get(level_num, "Unknown")
            else:
                _LOGGER.debug(f"WORKMODE not found in Q response from {self.miner_ip}, preserving previous value: {data.get('level')}")
            
            # Q does not use WORKLEVEL field - ignore it
            
            # Extract elapsed time (uptime)
            match = re.search(r'Elapsed\[(\d+)\]', response)
            if match:
                data["elapsed"] = int(match.group(1))
            
            # Extract DNA (serial number)
            match = re.search(r'DNA\[([^\]]+)\]', response)
            if match:
                data["serial"] = match.group(1)
                # Use DNA as unique identifier for mac
                data["mac"] = f"canaan_{match.group(1)}"
            
            # Extract firmware version
            match = re.search(r'Ver\[([^\]]+)\]', response)
            if match:
                data["firmware"] = match.group(1)
            
        except Exception as err:
            _LOGGER.error(f"Error parsing Q stats: {err}")
        
        return data

    def _parse_stats(self, response: str) -> dict:
        """Parse stats response based on model type."""
        if self.model_type == MODEL_NANO3S:
            return self._parse_stats_nano3s(response)
        elif self.model_type == MODEL_Q:
            return self._parse_stats_q(response)
        else:
            return self._parse_stats_mini3(response)

    def _get_default_data(self) -> dict:
        """Get default data structure based on model type."""
        if self.model_type == MODEL_NANO3S:
            data = DEFAULT_DATA_NANO3S.copy()
        elif self.model_type == MODEL_Q:
            data = DEFAULT_DATA_Q.copy()
        else:
            data = DEFAULT_DATA_MINI3.copy()
        data["ip"] = self.miner_ip
        data["mac"] = f"canaan_{self.miner_ip.replace('.', '_')}"
        data["model"] = self.model_name
        data["model_type"] = self.model_type
        return data

    async def _async_update_data(self):
        """Fetch data from miner."""
        try:
            _LOGGER.debug(f"Fetching data from {self.miner_ip} (model: {self.model_type})")
            
            # Get stats
            response = await self.api.get_stats()
            
            if not response:
                self._failure_count += 1
                
                if self._failure_count == 1:
                    _LOGGER.warning(f"Miner at {self.miner_ip} is offline - returning default data")
                    return self._get_default_data()
                
                raise UpdateFailed(f"Miner at {self.miner_ip} is offline")
            
            # Parse response
            data = self._parse_stats(response)
            
            # Reset failure count on success
            self._failure_count = 0
            
            _LOGGER.debug(
                f"Got data from {self.miner_ip}: "
                f"model={data.get('model')}, "
                f"hashrate={data.get('hashrate', 0):.2f} TH/s, "
                f"output_temp={data.get('output_temp', 0)}°C, "
                f"state={data.get('state')}, "
                f"mode={data.get('mode')}"
            )
            
            return data
            
        except Exception as err:
            self._failure_count += 1
            
            if self._failure_count == 1:
                _LOGGER.warning(f"Error fetching data from {self.miner_ip}: {err}")
                return self._get_default_data()
            
            _LOGGER.exception(f"Failed to fetch data from {self.miner_ip}")
            raise UpdateFailed(f"Error communicating with miner: {err}")

    @property
    def available(self) -> bool:
        """Return if miner is available."""
        return self._failure_count < 2
