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

**v0.1.4** — documented public release with current MQTT discovery behavior.

Milestone checklist:

- [x] Home Assistant Add-on Skeleton
- [x] rtl_433 Integration
- [x] MQTT Bridge
- [x] Home Assistant Discovery
- [x] Documentation
- [x] Release v0.1.4

## Install

1. **Settings → Add-ons → Add-on store → Repositories**
2. Add `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`
3. Install **RTL433 Acurite Bridge**, start it, and check the log

Full configuration details are in the add-on **Documentation** tab (`addon/DOCS.md`).

### If Home Assistant never shows an update

Supervisor keeps whatever Git branch it first cloned. If you originally added this repo while `scaffold` was checked out, it can stay stuck on **0.1.2** forever.

Fix:

1. Uninstall the add-on (optional but cleanest)
2. Add-on store → **Repositories** → remove this repository
3. Add it again as: `https://github.com/dcsubie/RTL433-Acurite-Bridge#main`
4. **⋮ → Check for updates**, then install/update to **0.1.4**

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
