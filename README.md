# RTL433-Acurite-Bridge

A modern Home Assistant add-on that bridges **rtl_433** weather station data into Home Assistant using MQTT Discovery.

## Features

- Supports RTL-SDR receivers
- Designed for Acurite weather stations
- Home Assistant MQTT Discovery
- Supervisor MQTT auto-configuration
- Device whitelist
- Diagnostic RSSI/SNR entities
- Multi-architecture builds (`amd64`, `aarch64`, `armv7`)
- Open Source (MIT)

## Status

**v0.1.2** — first documented public release candidate.

Milestone checklist:

- [x] Home Assistant Add-on Skeleton
- [x] rtl_433 Integration
- [x] MQTT Bridge
- [x] Home Assistant Discovery
- [x] Documentation
- [x] Release v0.1.2

## Install

1. **Settings → Add-ons → Add-on store → Repositories**
2. Add `https://github.com/dcsubie/RTL433-Acurite-Bridge`
3. Install **RTL433 Acurite Bridge**, start it, and check the log

Full configuration details are in the add-on **Documentation** tab (`addon/DOCS.md`).

## Planned Features

- MQTT device discovery migration (single device payload)
- Legacy topic compatibility
- Imperial unit field mapping
- Protocol presets in the UI
- Stronger MQTT reconnect handling

## Security

MQTT credentials and other secrets belong in the Home Assistant add-on configuration UI (or your local secrets), never in this repository, issues, or pull requests.

If you believe you found a security issue, please report it privately instead of opening a public issue that includes credentials, broker details, or device identifiers.

When sharing screenshots or logs, redact usernames, passwords, hostnames, IPs, and sensor/device IDs.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Joshua Ellis
