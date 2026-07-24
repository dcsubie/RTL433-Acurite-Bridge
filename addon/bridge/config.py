"""
Configuration handling for the RTL433 Acurite Bridge.
"""

from dataclasses import dataclass
import os


@dataclass
class Config:
    mqtt_host: str = "core-mosquitto"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic: str = "rtl_433"
    units: str = "si"
    whitelist: tuple[str, ...] = ()


def load_config() -> Config:
    """Load configuration from environment variables."""

    return Config(
        mqtt_host=os.getenv("MQTT_HOST", "core-mosquitto"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        mqtt_topic=os.getenv("MQTT_TOPIC", "rtl_433"),
        units=os.getenv("UNITS", "si"),
        whitelist=tuple(
            sensor_id.strip()
            for sensor_id in os.getenv("WHITELIST", "").split(",")
            if sensor_id.strip()
        ),
    )
