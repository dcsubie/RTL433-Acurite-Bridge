# Changelog

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
