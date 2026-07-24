"""
Home Assistant MQTT Discovery support.
"""

import logging

from mqtt import MQTTBridge
from sensors import SensorReading

LOGGER = logging.getLogger("rtl433-bridge.discovery")


class DiscoveryPublisher:
    def __init__(
        self,
        mqtt: MQTTBridge,
        topic_root: str,
        discovery_prefix: str = "homeassistant",
    ):
        self.mqtt = mqtt
        self.topic_root = topic_root
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
    ) -> None:
        """Publish a Home Assistant MQTT Discovery entity."""

        unique_id = f"{sensor.sensor_id}_{unique_suffix}"

        config_topic = (
            f"{self.discovery_prefix}/{component}/"
            f"{sensor.sensor_id}/{unique_suffix}/config"
        )

        state_topic = sensor.base_topic(self.topic_root)

        payload = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": value_template
            or f"{{{{ value_json.{unique_suffix} }}}}",
            "device": {
                "identifiers": [sensor.sensor_id],
                "name": sensor.device_name(),
                "manufacturer": "Acurite",
                "model": sensor.model,
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
            ),
            (
                "humidity",
                "Humidity",
                "humidity",
                "%",
                "measurement",
                None,
            ),
            (
                "wind_speed",
                "Wind Speed",
                None,
                "km/h",
                "measurement",
                None,
            ),
            (
                "wind_gust",
                "Wind Gust",
                None,
                "km/h",
                "measurement",
                None,
            ),
            (
                "wind_direction",
                "Wind Direction",
                None,
                "°",
                "measurement",
                None,
            ),
            (
                "rain_total",
                "Rain Total",
                "precipitation",
                "mm",
                "measurement",
                None,
            ),
            (
                "pressure",
                "Pressure",
                "atmospheric_pressure",
                "hPa",
                "measurement",
                None,
            ),
            (
                "rssi",
                "Signal Strength",
                None,
                None,
                None,
                "mdi:wifi",
            ),
        ]

        for field, name, device_class, unit, state_class, icon in sensor_map:
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
