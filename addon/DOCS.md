# RTL433 Acurite Bridge

Acurite-first bridge from **rtl_433** weather sensors into Home Assistant using MQTT Discovery.

This add-on is opinionated around a typical home setup (HA OS + Mosquitto + RTL-SDR + Acurite), while still allowing other rtl_433 protocols when needed.

## Who this is for

- You have an RTL-SDR stick plugged into the Home Assistant host
- You want Acurite weather sensors in Home Assistant with minimal MQTT YAML
- You are okay starting with Acurite defaults, then locking down with a whitelist

## Prerequisites

- Home Assistant OS or Supervised
- An RTL-SDR USB receiver on the Home Assistant host
- The [Mosquitto broker](https://github.com/home-assistant/addons/tree/master/mosquitto) add-on (recommended), or another MQTT broker
- MQTT integration enabled in Home Assistant

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on store**.
2. Open the three-dot menu → **Repositories**.
3. Add:

   `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`

4. Refresh the add-on store and install **RTL433 Acurite Bridge**.
5. Start the add-on and open **Log**.

You should see MQTT connect, the configured protocols, and eventually JSON/sensor activity when a station transmits.

### Updates not appearing

Use the `#main` repository URL above.

If an older Supervisor clone is stuck:

1. Remove this repository from the Add-on store
2. Re-add `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`
3. **Check for updates**, then install/update
4. Check **Settings → System → Logs → Supervisor** for git/`config.yaml` errors if needed

## Recommended setup path

1. Leave defaults as-is (`protocols` filled, `whitelist` empty, `units: si`)
2. Start the add-on and identify your sensor IDs from Log / HA devices
3. Put only your IDs in `whitelist` (for example `784`, `220`)
4. Restart the add-on

That keeps the add-on Acurite-focused for day-to-day use while still being discoverable for first-time setup.

## Configuration

| Option | Description |
| --- | --- |
| `mqtt_host` | MQTT broker hostname. Default `core-mosquitto`. |
| `mqtt_port` | MQTT broker port. Default `1883`. |
| `mqtt_username` | Optional. Leave blank to auto-fill from Supervisor MQTT when using the default host. |
| `mqtt_password` | Optional MQTT password. |
| `mqtt_topic` | Root MQTT topic for sensor state payloads. Default `rtl_433`. |
| `whitelist` | Optional rtl_433 sensor IDs to accept. Use `whitelist: []` (or clear all entries) to accept every decoded ID. Do not delete the key on older versions; from 0.1.12 omitted/empty both work. |
| `protocols` | rtl_433 protocol numbers (`-R`). Defaults target common Acurite devices. Empty = all decoders. |
| `units` | `si` (recommended) or `custom`. Keep `si` unless you know the bridge field mapping. |
| `frequency` | rtl_433 tuner frequency (`-f`). Default `433.92M`. |
| `gain` | Optional rtl_433 gain (`-g`). Blank = rtl_433 default. Try `20` / `30` / `40` / `auto` if the outdoor station is weak. |
| `ppm` | Optional crystal correction (`-p`). Try `20`, `-20`, `40`, or `-40` if nearby sensors decode but the 5n1 does not. |

### Default protocols (Acurite-first)

| Protocol | Typical devices |
| --- | --- |
| `11` | Acurite 609TXC temperature/humidity |
| `40` | Acurite 5n1 / 3n1 / Atlas / 592TXR / related |
| `41` | Acurite 986 fridge/freezer |
| `55` | Acurite 606TX temperature |
| `74` | Acurite 00275rm / 00276rm |

Optional Acurite protocols you can add if needed:

- `10` Acurite 896 rain gauge
- `163` Acurite 590TX

### Other brands

This add-on is still Acurite-first, but you can add other rtl_433 protocol numbers to `protocols`.

1. Find the protocol ID from [`rtl_433` supported devices](https://github.com/merbanan/rtl_433)
2. Add that number to `protocols`
3. Restart and confirm packets in the Log
4. Whitelist only your sensor IDs

Manufacturer is labeled **Acurite** when the rtl_433 model name contains `Acurite`; otherwise it is labeled **rtl_433**.

### MQTT credentials

If `mqtt_host` is `core-mosquitto` and `mqtt_username` is blank, the add-on asks Supervisor for Mosquitto connection details automatically.

To use an external broker, set `mqtt_host` (and credentials if required) explicitly.

Never put real passwords in GitHub issues, screenshots, or this repository.

The bridge retries MQTT connect with backoff while the broker starts, and reconnects if the connection drops later.

## How it works

1. `rtl_433` decodes radio packets from the RTL-SDR stick as JSON
2. The Python bridge normalizes each packet and publishes state to MQTT
3. Home Assistant MQTT Discovery creates devices and entities automatically

### MQTT topics

| Topic | Purpose |
| --- | --- |
| `rtl_433/<sensor_id>` | Retained JSON state for one sensor |
| `rtl_433/bridge/status` | Bridge availability (`online` / `offline`) |
| `homeassistant/device/<sensor_id>/config` | MQTT device discovery (all entities for one station) |

On upgrade from older versions, the add-on migrates away from the previous
per-entity discovery topics (`homeassistant/sensor/.../config`) while keeping
the same entity `unique_id`s so existing HA entities should not duplicate.

### Discovered entities

Depending on what the station reports:

- Temperature, humidity, pressure
- Wind speed, wind gust, wind direction
- Rain total
- Battery (binary sensor)
- RSSI / SNR (diagnostic)

## Troubleshooting

- **No devices:** confirm the RTL-SDR is attached, check the add-on Log for rtl_433 startup, and verify your protocol list includes your sensor family
- **Too many devices:** set `whitelist` to only your sensor IDs
- **Acurite display updates but Home Assistant does not:** the outdoor station is transmitting. Check the add-on Log for `Packet id=` / `Heard`. If only a nearby sensor (like a 609TXC) appears, raise `gain`, try small `ppm` values, or nudge `frequency` (for example `433.9M` / `434.0M`). From 0.1.15 these are add-on options.
- **Station stopped updating after an add-on update:** check the Log for `Active whitelist`, `Heard sensor id=...`, `Published ...`, and `Skipping sensor ...`. If your station ID never appears in `Heard`, rtl_433 is not decoding it. If it is `Skipping`, fix `whitelist`. From 0.1.11 onward, partial 5n1 packets are merged; from 0.1.13 onward startup no longer blocks the rtl_433 pipe while seeding MQTT
- **Cannot clear whitelist (Missing option 'whitelist'):** set `whitelist: []` in YAML, or update to 0.1.12+ which allows an empty/omitted list. Do not remove the `whitelist` key on older versions
- **Finding a missing 5n1 ID:** temporarily use `whitelist: []`, restart, and watch the Log for `Heard sensor id=...`. A battery change can give the station a new ID
- **Everything weaker than before:** try higher `gain`, small `ppm` corrections, reseat the USB dongle, and compare time-to-first-`Heard` against a known-good window
- **Entities unavailable:** confirm the add-on is running and MQTT is reachable
- **Wrong/empty sensor values with `custom` units:** switch back to `si`; the bridge currently maps SI field names
- After Home Assistant restarts, retained state should restore the last reading until a new radio packet arrives

## Supported architectures

- `amd64`
- `aarch64`
- `armv7`

## Support

- Source: https://github.com/dcsubie/RTL433-Acurite-Bridge
- Report bugs with redacted logs (no passwords, IPs, or private device IDs)
