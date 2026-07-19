"""
Home Assistant MQTT Discovery support.
"""

import json
import logging

from sensors import SensorReading
from mqtt import MQTTBridge

LOGGER = logging.getLogger("rtl433-bridge.discovery")


class DiscoveryPublisher:
    def __init__(self, mqtt: MQTTBridge, discovery_prefix: str = "homeassistant"):
        self.mqtt = mqtt
        self.discovery_prefix = discovery_prefix

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

        unique_id = f"{sensor.sensor_id}_{unique_suffix}"

        config_topic = (
            f"{self.discovery_prefix}/sensor/"
            f"{sensor.sensor_id}/{unique_suffix}/config"
        )

        state_topic = sensor.base_topic("rtl_433")

        payload = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": "{{ value_json.%s }}" % unique_suffix,
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

        self.mqtt.client.publish(
            config_topic,
            json.dumps(payload),
            retain=True,
        )

        LOGGER.info("Published discovery for %s", name)

    def publish_all(self, sensor: SensorReading):

        if sensor.temperature is not None:
            self.publish_sensor(
                sensor,
                "Temperature",
                "temperature",
                device_class="temperature",
                unit="°C",
            )

        if sensor.humidity is not None:
            self.publish_sensor(
                sensor,
                "Humidity",
                "humidity",
                device_class="humidity",
                unit="%",
            )

        if sensor.wind_speed is not None:
            self.publish_sensor(
                sensor,
                "Wind Speed",
                "wind_speed",
                unit="km/h",
            )

        if sensor.wind_gust is not None:
            self.publish_sensor(
                sensor,
                "Wind Gust",
                "wind_gust",
                unit="km/h",
            )

        if sensor.wind_direction is not None:
            self.publish_sensor(
                sensor,
                "Wind Direction",
                "wind_direction",
                unit="°",
            )

        if sensor.rain_total is not None:
            self.publish_sensor(
                sensor,
                "Rain Total",
                "rain_total",
                device_class="precipitation",
                unit="mm",
            )

        if sensor.pressure is not None:
            self.publish_sensor(
                sensor,
                "Pressure",
                "pressure",
                device_class="atmospheric_pressure",
                unit="hPa",
            )

        if sensor.battery_ok is not None:
            self.publish_sensor(
                sensor,
                "Battery",
                "battery_ok",
                device_class="battery",
            )

        if sensor.rssi is not None:
            self.publish_sensor(
                sensor,
                "Signal Strength",
                "rssi",
                icon="mdi:wifi",
                state_class=None,
            )
