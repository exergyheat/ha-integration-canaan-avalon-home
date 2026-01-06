# Canaan Avalon Miner Integration

Monitor and control Canaan Avalon bitcoin miners (Avalon Mini 3, Nano 3s, Q) directly in Home Assistant.

## Features

### Sensors
- **Hashrate** - Current mining hashrate in TH/s
- **Temperatures** - Internal, output, and limit temperatures
- **Fan Speed** - Fan speed percentage
- **WiFi Signal** - Signal strength (disabled by default)
- **State** - Miner state (Initializing, Working, Idle, Fault)
- **Work Mode** - Current mode (Heating, Mining, Night)
- **Work Level** - Performance level (Super, Eco)

### Controls
- **Power Switch** - Turn miner on/off
- **Work Mode Select** - Choose between Heating, Mining, or Night mode
- **Work Level Select** - Choose between Super or Eco performance
- **Update Button** - Manual data refresh

## Configuration

After installation via HACS:

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**Canaan Avalon Miner**"
3. Enter your miner's IP address
4. Configure name, port (4028 default), and scan interval (15s default)

## Work Modes

- **Heating** - Optimized for heat output, lower hashrate
- **Mining** - Optimized for mining performance
- **Night** - Quiet mode with reduced fan speed

## Work Levels

- **Super** - Maximum performance
- **Eco** - Energy-efficient mode

## Compatibility

Tested with:
- Canaan Avalon Mini 3
- Canaan Avalon Q
- Canaan Avalon Nano 3s

## Requirements

- Home Assistant 2023.1 or newer
- Canaan Avalon miner on your network
- Access to miner's IP address and port 4028

## Support

- **Integration Issues**: [GitHub Issues](https://github.com/exergyheat/ha-integration-canaan/issues)
- **Canaan Support**: https://canaan.io
