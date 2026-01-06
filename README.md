# ha-integration-canaan-avalon-home
Home Assistant Integration for Canaan Avalon Miners

# Canaan Avalon Home Miner Integration for Home Assistant

This custom integration allows you to monitor and control Canaan Avalon bitcoin miners (including Avalon Mini 3, Avalon Nano 3s and Avalon Q) in Home Assistant through an easy-to-use UI configuration.

## Features

### Sensors
- **Hashrate** - Current mining hashrate in TH/s
- **Internal Temperature** - Internal miner temperature in °C
- **Output Temperature** - Output air temperature in °C
- **Limit Temperature** - Temperature limit setting in °C
- **Fan Speed** - Fan speed percentage
- **WiFi Signal** - WiFi signal strength in dBm (disabled by default)
- **State** - Miner state (Initializing, Working, Idle, Fault)
- **Work Mode** - Current work mode (Heating, Mining, Night)
- **Work Level** - Current work level (Super, Eco)

### Controls
- **Power Switch** - Turn the miner on/off
- **Work Mode Select** - Choose between Heating, Mining, or Night mode
- **Work Level Select** - Choose between Super or Eco performance level
- **Update Button** - Manually trigger an immediate data refresh

## Installation

1. Copy the `canaan` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/canaan/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "**Canaan Avalon Miner**"

## Setup via UI

### Adding Your First Miner

1. Click **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**Canaan Avalon Miner**" and select it
3. **Step 1 - IP Address**: Enter your miner's IP address (e.g., `172.16.0.81`)
4. **Step 2 - Configuration**:
   - **Name**: Enter a friendly name (e.g., "Exergy Office Mini 3")
   - **Port**: Leave as 4028 (default) unless you changed it
   - **Scan Interval**: Leave as 15 seconds (default) or adjust as needed
5. Click **Submit**

Your miner will be added as a device with all sensors and controls!

### Adding Additional Miners

1. Go to **Settings** → **Devices & Services**
2. Find the **Canaan Avalon Miner** integration
3. Click **Add Entry** (the + button)
4. Repeat the setup steps above for each additional miner

### Configuring Options

You can change the port and scan interval after setup:

1. Go to **Settings** → **Devices & Services**
2. Find your miner device
3. Click **Configure**
4. Adjust settings as needed

## Usage

After adding a miner, the integration creates:

### Entities Created (per miner)

#### Sensors
- `sensor.{name}_hashrate`
- `sensor.{name}_internal_temperature`
- `sensor.{name}_output_temperature`
- `sensor.{name}_limit_temperature`
- `sensor.{name}_fan_speed`
- `sensor.{name}_wifi_signal` (disabled by default)
- `sensor.{name}_state`
- `sensor.{name}_work_mode`
- `sensor.{name}_work_level`

#### Controls
- `switch.{name}_power` - Turn miner on/off
- `select.{name}_work_mode` - Select work mode (Heating/Mining/Night)
- `select.{name}_work_level` - Select work level (Super/Eco)
- `button.{name}_update` - Manually refresh miner data

## Work Modes Explained

- **Heating (0)** - Optimized for heating output, lower hashrate
- **Mining (1)** - Optimized for mining performance
- **Night (2)** - Quiet mode with reduced fan speed and power

## Work Levels Explained

- **Super (0)** - Maximum performance
- **Eco (-1)** - Energy-efficient mode

## Protocol Details

The integration communicates with Canaan Avalon miners using the custom Avalon protocol over TCP port 4028:

- **Stats Command**: `{"command":"estats"}` - Get miner statistics
- **Set Work Mode**: `ascset|0,workmode,set,{value}` - Set work mode (0/1/2)
- **Set Work Level**: `ascset|0,worklevel,set,{value}` - Set work level (0/-1)
- **Power On**: `ascset|0,softon,1:{timestamp}` - Turn on miner
- **Power Off**: `ascset|0,softoff,1:{timestamp}` - Turn off miner

## Troubleshooting

### Integration not appearing in Add Integration
- Ensure you've restarted Home Assistant after copying the files
- Check that the `canaan` folder is in `/config/custom_components/`
- Check Home Assistant logs for any errors

### Miner shows as unavailable
- Verify the miner's IP address is correct
- Ensure the miner is powered on and connected to your network
- Check that port 4028 is accessible (no firewall blocking)
- Try pinging the miner IP from your Home Assistant host

### Commands not working
- Check Home Assistant logs for error messages
- Verify the miner firmware supports the commands
- Some older firmware versions may have limited command support

### Data not updating
- Check the scan interval setting (default 15 seconds)
- Verify network connectivity to the miner
- Check for errors in Home Assistant logs
- Try reloading the integration

### Removing a Miner

1. Go to **Settings** → **Devices & Services**
2. Find the **Canaan Avalon Miner** integration
3. Find the miner you want to remove
4. Click the three dots menu → **Delete**

## Compatibility

Tested with:
- Canaan Avalon Mini 3
- Canaan Avalon Q
- Canaan Avalon Nano 3s

Should work with other Canaan Avalon miners that support the estats protocol.

## Default Settings

- **Port**: 4028
- **Scan Interval**: 15 seconds (adjustable from 5-300 seconds)

## Support

For issues, feature requests, or questions, please open an issue on GitHub.

## License

MIT License
