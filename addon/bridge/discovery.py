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
        self.discovered: set[str] = set()

    def publish_sensor(
        self,
        sensor: SensorReading,
        name: str,
        unique_suffix: str,
        device_class: str | None = None,
        unit: str | None = None,
        state_class: str | None = "measurement",
        icon: str | None = None,
    ) -> None:
        """Publish a Home Assistant MQTT Discovery entity."""

        unique_id = f"{sensor.sensor_id}_{unique_suffix}"

        config_topic = (
            f"{self.discovery_prefix}/sensor/"
            f"{sensor.sensor_id}/{unique_suffix}/config"
        )

        state_topic = sensor.base_topic(self.topic_root)

        payload = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{unique_suffix} }}}}",
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
                "battery_ok",
                "Battery",
                "battery",
                None,
                None,
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
            if getattr(sensor, field) is not None:
                self.publish_sensor(
                    sensor=sensor,
                    name=name,
                    unique_suffix=field,
                    device_class=device_class,
                    unit=unit,
                    state_class=state_class,
                    icon=icon,
                )

    def publish_once(self, sensor: SensorReading) -> None:
        """Only publish discovery once per sensor."""

        if sensor.sensor_id in self.discovered:
            return

        self.publish_all(sensor)
        self.discovered.add(sensor.sensor_id)
