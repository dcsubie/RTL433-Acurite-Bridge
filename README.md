# RTL433-Acurite-Bridge

Acurite-first Home Assistant add-on that bridges **rtl_433** weather sensors into Home Assistant with MQTT Discovery.

Defaults are tuned for a common home setup:

- Home Assistant OS + Mosquitto
- USB RTL-SDR on the HA host
- Acurite 433 MHz weather sensors
- Metric (`si`) units

Other rtl_433 brands can work by changing the protocol list. This project stays focused on Acurite weather stations first.

## Quick start

1. Plug in an RTL-SDR stick
2. Install/start the official **Mosquitto broker** add-on
3. Enable the **MQTT** integration in Home Assistant
4. Add this repository: `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`
5. Install **RTL433 Acurite Bridge**, start it, and watch the Log

Leave MQTT username/password blank if you use Mosquitto on this HA instance.

## Features

- Acurite-first protocol defaults (`11`, `40`, `41`, `55`, `74`)
- Home Assistant MQTT Discovery
- Supervisor MQTT auto-configuration
- Optional sensor ID whitelist (recommended after first run)
- Bridge availability + retained sensor state
- Diagnostic RSSI/SNR entities
- Multi-architecture builds (`amd64`, `aarch64`, `armv7`)
- MIT licensed

## Recommended first-run flow

1. Start with the default protocols and an **empty whitelist**
2. Confirm your stations appear in the add-on Log / MQTT / HA devices
3. Copy your sensor IDs into **whitelist** so neighbor stations are ignored
4. Keep `units: si` unless you know you need otherwise

Full option reference, protocol table, and troubleshooting are in the add-on **Documentation** tab (`addon/DOCS.md`).

## Status

**v0.1.10** — whitelist enforcement fix, protocol `-R` flags, and MQTT device discovery.

## Planned Features

- Imperial unit field mapping
- Protocol presets in the UI
- Stale-sensor expiry / unavailable after quiet period

## Security

MQTT credentials and other secrets belong in the Home Assistant add-on configuration UI, never in this repository, issues, or pull requests.

If you believe you found a security issue, please report it privately instead of opening a public issue that includes credentials, broker details, or device identifiers.

When sharing screenshots or logs, redact usernames, passwords, hostnames, IPs, and sensor/device IDs.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Joshua Ellis
