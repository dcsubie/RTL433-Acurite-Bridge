"""
Home Assistant MQTT Discovery support.

Uses MQTT device discovery so each weather station becomes one HA device
with multiple components. Existing entity unique_ids are preserved.
"""

from __future__ import annotations

import logging
from typing import Any

from mqtt import (
    MQTTBridge,
    PAYLOAD_AVAILABLE,
    PAYLOAD_NOT_AVAILABLE,
)
from sensors import SensorReading

LOGGER = logging.getLogger("rtl433-bridge.discovery")

SENSOR_MAP = (
    (
        "temperature",
        "Temperature",
        "temperature",
        "°C",
        "measurement",
        None,
        None,
        "sensor",
    ),
    (
        "humidity",
        "Humidity",
        "humidity",
        "%",
        "measurement",
        None,
        None,
        "sensor",
    ),
    (
        "wind_speed",
        "Wind Speed",
        "wind_speed",
        "km/h",
        "measurement",
        None,
        None,
        "sensor",
    ),
    (
        "wind_gust",
        "Wind Gust",
        "wind_speed",
        "km/h",
        "measurement",
        None,
        None,
        "sensor",
    ),
    (
        "wind_direction",
        "Wind Direction",
        None,
        "°",
        "measurement",
        "mdi:compass",
        None,
        "sensor",
    ),
    (
        "rain_total",
        "Rain Total",
        "precipitation",
        "mm",
        "total_increasing",
        None,
        None,
        "sensor",
    ),
    (
        "pressure",
        "Pressure",
        "atmospheric_pressure",
        "hPa",
        "measurement",
        None,
        None,
        "sensor",
    ),
    (
        "rssi",
        "Signal Strength",
        None,
        None,
        "measurement",
        "mdi:wifi",
        "diagnostic",
        "sensor",
    ),
    (
        "snr",
        "Signal-to-Noise",
        None,
        "dB",
        "measurement",
        "mdi:signal",
        "diagnostic",
        "sensor",
    ),
)


class DiscoveryPublisher:
    def __init__(
        self,
        mqtt: MQTTBridge,
        topic_root: str,
        availability_topic: str,
        origin_name: str,
        origin_version: str,
        origin_support_url: str,
        discovery_prefix: str = "homeassistant",
    ):
        self.mqtt = mqtt
        self.topic_root = topic_root
        self.availability_topic = availability_topic
        self.origin_name = origin_name
        self.origin_version = origin_version
        self.origin_support_url = origin_support_url
        self.discovery_prefix = discovery_prefix

        # sensor_id -> component_key -> component config
        self.components: dict[str, dict[str, dict[str, Any]]] = {}
        # sensor_id -> latest device metadata used in discovery
        self.devices: dict[str, dict[str, Any]] = {}
        # sensor_ids that already completed single->device migration cleanup
        self.migrated: set[str] = set()

    def _legacy_config_topic(
        self,
        sensor_id: str,
        component: str,
        unique_suffix: str,
    ) -> str:
        return (
            f"{self.discovery_prefix}/{component}/"
            f"{sensor_id}/{unique_suffix}/config"
        )

    def _device_config_topic(self, sensor_id: str) -> str:
        return f"{self.discovery_prefix}/device/{sensor_id}/config"

    def _build_component(
        self,
        sensor: SensorReading,
        name: str,
        unique_suffix: str,
        device_class: str | None = None,
        unit: str | None = None,
        state_class: str | None = "measurement",
        icon: str | None = None,
        component: str = "sensor",
        value_template: str | None = None,
        payload_on: str | None = None,
        payload_off: str | None = None,
        entity_category: str | None = None,
    ) -> dict[str, Any]:
        unique_id = f"{sensor.sensor_id}_{unique_suffix}"
        payload: dict[str, Any] = {
            "platform": component,
            "name": name,
            "unique_id": unique_id,
            "default_entity_id": f"{component}.{unique_id}",
            "value_template": value_template
            or f"{{{{ value_json.{unique_suffix} }}}}",
        }

        if device_class:
            payload["device_class"] = device_class
        if unit:
            payload["unit_of_measurement"] = unit
        if state_class:
            payload["state_class"] = state_class
        if icon:
            payload["icon"] = icon
        if entity_category:
            payload["entity_category"] = entity_category
        if payload_on is not None:
            payload["payload_on"] = payload_on
        if payload_off is not None:
            payload["payload_off"] = payload_off

        return payload

    def _migrate_legacy_discovery(
        self,
        sensor_id: str,
        components: dict[str, dict[str, Any]],
    ) -> None:
        """Unload old per-entity discovery topics before switching to device discovery."""

        for unique_suffix, component_config in components.items():
            platform = component_config["platform"]
            legacy_topic = self._legacy_config_topic(
                sensor_id,
                platform,
                unique_suffix,
            )
            self.mqtt.publish_json(
                legacy_topic,
                {"migrate_discovery": True},
                retain=True,
            )
            LOGGER.info(
                "Requested discovery migration for legacy topic %s",
                legacy_topic,
            )

    def _clear_legacy_discovery(
        self,
        sensor_id: str,
        components: dict[str, dict[str, Any]],
    ) -> None:
        """Clear retained single-component discovery payloads after migration."""

        for unique_suffix, component_config in components.items():
            platform = component_config["platform"]
            legacy_topic = self._legacy_config_topic(
                sensor_id,
                platform,
                unique_suffix,
            )
            self.mqtt.publish_text(legacy_topic, "", retain=True)
            LOGGER.info("Cleared legacy discovery topic %s", legacy_topic)

    def _publish_device_discovery(self, sensor_id: str) -> None:
        components = self.components.get(sensor_id, {})
        device = self.devices.get(sensor_id)
        if not components or not device:
            return

        migrating = sensor_id not in self.migrated
        if migrating:
            self._migrate_legacy_discovery(sensor_id, components)

        payload = {
            "device": device,
            "origin": {
                "name": self.origin_name,
                "sw_version": self.origin_version,
                "support_url": self.origin_support_url,
            },
            "availability_topic": self.availability_topic,
            "payload_available": PAYLOAD_AVAILABLE,
            "payload_not_available": PAYLOAD_NOT_AVAILABLE,
            "state_topic": f"{self.topic_root}/{sensor_id}",
            "components": components,
        }

        topic = self._device_config_topic(sensor_id)
        self.mqtt.publish_json(topic, payload, retain=True)
        LOGGER.info(
            "Published device discovery for %s (%s components)",
            sensor_id,
            len(components),
        )

        if migrating:
            self._clear_legacy_discovery(sensor_id, components)
            self.migrated.add(sensor_id)

    def publish_all(self, sensor: SensorReading) -> None:
        """Publish or update device discovery for every available sensor value."""

        sensor_components = self.components.setdefault(sensor.sensor_id, {})
        changed = False

        self.devices[sensor.sensor_id] = {
            "identifiers": [sensor.sensor_id],
            "name": sensor.device_name(),
            "manufacturer": sensor.manufacturer(),
            "model": sensor.model,
            "sw_version": self.origin_version,
        }

        for (
            field,
            name,
            device_class,
            unit,
            state_class,
            icon,
            entity_category,
            component,
        ) in SENSOR_MAP:
            if getattr(sensor, field) is None or field in sensor_components:
                continue

            sensor_components[field] = self._build_component(
                sensor=sensor,
                name=name,
                unique_suffix=field,
                device_class=device_class,
                unit=unit,
                state_class=state_class,
                icon=icon,
                component=component,
                entity_category=entity_category,
            )
            changed = True

        if (
            sensor.battery_ok is not None
            and "battery_ok" not in sensor_components
        ):
            sensor_components["battery_ok"] = self._build_component(
                sensor=sensor,
                name="Battery",
                unique_suffix="battery_ok",
                device_class="battery",
                state_class=None,
                component="binary_sensor",
                value_template="{{ 'OFF' if value_json.battery_ok else 'ON' }}",
                payload_on="ON",
                payload_off="OFF",
            )
            changed = True

        # Republish when components change, or once to migrate an existing device.
        if changed or sensor.sensor_id not in self.migrated:
            self._publish_device_discovery(sensor.sensor_id)

    def publish_available(self, sensor: SensorReading) -> None:
        """Publish discovery for values not previously announced for this sensor."""

        self.publish_all(sensor)
