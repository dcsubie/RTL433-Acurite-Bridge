"""
Home Assistant MQTT Discovery support.
"""

import logging

from mqtt import (
    MQTTBridge,
    PAYLOAD_AVAILABLE,
    PAYLOAD_NOT_AVAILABLE,
)
from sensors import SensorReading

LOGGER = logging.getLogger("rtl433-bridge.discovery")


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
        self.discovered: set[tuple[str, str]] = set()

    def publish_sensor(
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
    ) -> None:
        """Publish a Home Assistant MQTT Discovery entity.

        Discovery topic layout is unchanged so existing entities keep working:
        ``{prefix}/{component}/{sensor_id}/{unique_suffix}/config``
        """

        unique_id = f"{sensor.sensor_id}_{unique_suffix}"

        config_topic = (
            f"{self.discovery_prefix}/{component}/"
            f"{sensor.sensor_id}/{unique_suffix}/config"
        )

        state_topic = sensor.base_topic(self.topic_root)

        payload = {
            "name": name,
            "unique_id": unique_id,
            "default_entity_id": f"{component}.{unique_id}",
            "state_topic": state_topic,
            "value_template": value_template
            or f"{{{{ value_json.{unique_suffix} }}}}",
            "availability_topic": self.availability_topic,
            "payload_available": PAYLOAD_AVAILABLE,
            "payload_not_available": PAYLOAD_NOT_AVAILABLE,
            "origin": {
                "name": self.origin_name,
                "sw_version": self.origin_version,
                "support_url": self.origin_support_url,
            },
            "device": {
                "identifiers": [sensor.sensor_id],
                "name": sensor.device_name(),
                "manufacturer": sensor.manufacturer(),
                "model": sensor.model,
                "sw_version": self.origin_version,
            },
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

        self.mqtt.publish_json(
            config_topic,
            payload,
            retain=True,
        )

        LOGGER.info("Published discovery for %s", unique_id)

    def publish_all(self, sensor: SensorReading) -> None:
        """Publish discovery for every available sensor value."""

        sensor_map = [
            (
                "temperature",
                "Temperature",
                "temperature",
                "°C",
                "measurement",
                None,
                None,
            ),
            (
                "humidity",
                "Humidity",
                "humidity",
                "%",
                "measurement",
                None,
                None,
            ),
            (
                "wind_speed",
                "Wind Speed",
                "wind_speed",
                "km/h",
                "measurement",
                None,
                None,
            ),
            (
                "wind_gust",
                "Wind Gust",
                "wind_speed",
                "km/h",
                "measurement",
                None,
                None,
            ),
            (
                "wind_direction",
                "Wind Direction",
                None,
                "°",
                "measurement",
                "mdi:compass",
                None,
            ),
            (
                "rain_total",
                "Rain Total",
                "precipitation",
                "mm",
                "total_increasing",
                None,
                None,
            ),
            (
                "pressure",
                "Pressure",
                "atmospheric_pressure",
                "hPa",
                "measurement",
                None,
                None,
            ),
            (
                "rssi",
                "Signal Strength",
                None,
                None,
                "measurement",
                "mdi:wifi",
                "diagnostic",
            ),
            (
                "snr",
                "Signal-to-Noise",
                None,
                "dB",
                "measurement",
                "mdi:signal",
                "diagnostic",
            ),
        ]

        for (
            field,
            name,
            device_class,
            unit,
            state_class,
            icon,
            entity_category,
        ) in sensor_map:
            discovery_key = (sensor.sensor_id, field)
            if getattr(sensor, field) is not None and discovery_key not in self.discovered:
                self.publish_sensor(
                    sensor=sensor,
                    name=name,
                    unique_suffix=field,
                    device_class=device_class,
                    unit=unit,
                    state_class=state_class,
                    icon=icon,
                    entity_category=entity_category,
                )
                self.discovered.add(discovery_key)

        battery_key = (sensor.sensor_id, "battery_ok")
        if sensor.battery_ok is not None and battery_key not in self.discovered:
            self.publish_sensor(
                sensor=sensor,
                name="Battery",
                unique_suffix="battery_ok",
                device_class="battery",
                state_class=None,
                component="binary_sensor",
                value_template=(
                    "{{ 'OFF' if value_json.battery_ok else 'ON' }}"
                ),
                payload_on="ON",
                payload_off="OFF",
            )
            self.discovered.add(battery_key)

    def publish_available(self, sensor: SensorReading) -> None:
        """Publish discovery for values not previously announced for this sensor."""

        self.publish_all(sensor)
