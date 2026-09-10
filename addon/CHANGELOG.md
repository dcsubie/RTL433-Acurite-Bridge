# Changelog

## 0.1.8

- Switch Home Assistant MQTT discovery to device discovery (one device payload
  per station)
- Migrate existing single-entity discovery topics safely while keeping the same
  entity `unique_id`s
- Update docs for the new discovery topic layout

## 0.1.7

- Position the add-on as Acurite-first but usable by others
- Document default protocol meanings and a recommended first-run whitelist flow
- Log human-readable protocol labels at startup
- Label non-Acurite devices as `rtl_433` instead of hardcoding Acurite

## 0.1.6

- Fix bashio parsing of `protocols` and `whitelist` arrays so configured values
  are logged and actually applied to rtl_433 / the MQTT bridge

## 0.1.5

- Retry MQTT connect with exponential backoff while the broker starts
- Enable paho automatic reconnect after unexpected disconnects
- Republish availability on reconnect
- Remove the stale `scaffold` branch so Supervisor cannot stay stuck on 0.1.2

## 0.1.4

- Version bump so Home Assistant can detect a fresh update
- Default Docker `BUILD_FROM` for current Supervisor builds
- Enable `uart` for RTL-SDR devices
- Drop unused legacy `map: config:rw` mount
- Docs: how to force Supervisor onto the `main` branch if updates never appear

## 0.1.3

- Version bump so Home Assistant offers an update from earlier 0.1.2 builds
- Includes the MQTT modernization already landed on main: discovery origin,
  availability/last-will, retained states, Supervisor MQTT auto-config, and
  improved sensor metadata

## 0.1.2

- Add MQTT discovery `origin` and `default_entity_id` for current Home Assistant
- Publish bridge availability (`rtl_433/bridge/status`) with MQTT last-will
- Retain sensor state topics so readings survive Home Assistant restarts
- Auto-configure MQTT from Supervisor when using the default Mosquitto host
- Improve sensor metadata (rain `total_increasing`, wind `wind_speed`, diagnostic RSSI/SNR)
- Add add-on documentation, changelog, and English configuration translations
- Set `startup: application` and declare `mqtt:want`

## 0.1.1

- Initial public add-on skeleton with rtl_433 → MQTT Discovery bridge
- Multi-architecture build metadata (`amd64`, `aarch64`, `armv7`)
- Configurable MQTT broker, topic, protocol list, whitelist, and units
