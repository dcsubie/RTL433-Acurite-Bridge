# RTL433 Acurite Bridge

Bridges **rtl_433** weather station data into Home Assistant using MQTT Discovery.

## Prerequisites

- Home Assistant OS or Supervised
- An RTL-SDR USB receiver plugged into the Home Assistant host
- The [Mosquitto broker](https://github.com/home-assistant/addons/tree/master/mosquitto) add-on (recommended), or another MQTT broker
- MQTT integration enabled in Home Assistant

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on store**.
2. Open the three-dot menu → **Repositories**.
3. Add (pin `main` so Supervisor cannot stay on an old branch):

   `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`

4. Refresh the add-on store and install **RTL433 Acurite Bridge**.
5. Start the add-on and open **Log** to confirm rtl_433 and the MQTT bridge started.

### Updates not appearing

Use the `#main` repository URL above. The old `scaffold` branch has been removed.

If an older Supervisor clone is still stuck:

1. Remove this repository from the Add-on store.
2. Re-add `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`.
3. Use **Check for updates**, then install/update to the latest version.
4. If needed, check **Settings → System → Logs → Supervisor** for `Can't read .../config.yaml` or git pull errors.

## Configuration

| Option | Description |
| --- | --- |
| `mqtt_host` | MQTT broker hostname. Default `core-mosquitto`. |
| `mqtt_port` | MQTT broker port. Default `1883`. |
| `mqtt_username` | Optional MQTT username. Leave blank to auto-fill from the Supervisor MQTT service when using the default host. |
| `mqtt_password` | Optional MQTT password. |
| `mqtt_topic` | Root MQTT topic for sensor state payloads. Default `rtl_433`. |
| `whitelist` | Optional list of rtl_433 sensor IDs to accept. Empty = accept all. |
| `protocols` | rtl_433 protocol numbers to enable. Defaults target common Acurite devices. |
| `units` | `si` (recommended) or `custom`. `si` passes `-C si` to rtl_433. |

### MQTT credentials

If `mqtt_host` is left at `core-mosquitto` and `mqtt_username` is blank, the add-on asks the Supervisor for Mosquitto connection details automatically.

To use an external broker, set `mqtt_host` (and credentials if required) explicitly.

Never put real passwords in GitHub issues, screenshots, or this repository.

The bridge retries MQTT connect with backoff while the broker starts, and automatically reconnects if the connection drops later.

## How it works

1. `rtl_433` decodes radio packets from the RTL-SDR stick as JSON.
2. The Python bridge normalizes each packet and publishes state to MQTT.
3. Home Assistant MQTT Discovery creates devices and entities automatically.

### MQTT topics

| Topic | Purpose |
| --- | --- |
| `rtl_433/<sensor_id>` | Retained JSON state for one sensor |
| `rtl_433/bridge/status` | Bridge availability (`online` / `offline`) |
| `homeassistant/.../<sensor_id>/<field>/config` | MQTT Discovery configs |

### Discovered entities

Depending on what the station reports:

- Temperature, humidity, pressure
- Wind speed, wind gust, wind direction
- Rain total
- Battery (binary sensor)
- RSSI / SNR (diagnostic)

## Tips

- Keep `units` set to `si` unless you know you need otherwise. The bridge currently maps SI field names from rtl_433.
- Use `whitelist` once you know your sensor IDs to ignore neighbors' weather stations.
- If entities show **Unavailable**, check that the add-on is running and MQTT is reachable.
- After Home Assistant restarts, retained state should restore the last reading until a new radio packet arrives.

## Supported architectures

- `amd64`
- `aarch64`
- `armv7`

## Support

- Source: https://github.com/dcsubie/RTL433-Acurite-Bridge
- Report bugs with redacted logs (no passwords, IPs, or device IDs you want private)
