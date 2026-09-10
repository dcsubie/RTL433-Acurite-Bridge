"""
Configuration handling for the RTL433 Acurite Bridge.
"""

from dataclasses import dataclass
import os


def _parse_id_list(raw: str) -> tuple[str, ...]:
    """Parse a comma-separated list of sensor IDs into normalized strings."""

    return tuple(
        sensor_id.strip()
        for sensor_id in raw.split(",")
        if sensor_id.strip() and sensor_id.strip().lower() != "null"
    )


@dataclass
class Config:
    mqtt_host: str = "core-mosquitto"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic: str = "rtl_433"
    units: str = "si"
    whitelist: tuple[str, ...] = ()
    addon_name: str = "RTL433 Acurite Bridge"
    addon_version: str = "0.1.13"
    addon_support_url: str = "https://github.com/dcsubie/RTL433-Acurite-Bridge"

    @property
    def availability_topic(self) -> str:
        """Return the shared bridge availability topic."""
        return f"{self.mqtt_topic}/bridge/status"


def load_config() -> Config:
    """Load configuration from environment variables."""

    # Prefer RTL433_WHITELIST; fall back to WHITELIST for older run.sh versions.
    whitelist_raw = os.getenv(
        "RTL433_WHITELIST",
        os.getenv("WHITELIST", ""),
    )

    return Config(
        mqtt_host=os.getenv("MQTT_HOST", "core-mosquitto"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        mqtt_topic=os.getenv("MQTT_TOPIC", "rtl_433"),
        units=os.getenv("UNITS", "si"),
        whitelist=_parse_id_list(whitelist_raw),
        addon_name=os.getenv("ADDON_NAME", "RTL433 Acurite Bridge"),
        addon_version=os.getenv("ADDON_VERSION", "0.1.13"),
        addon_support_url=os.getenv(
            "ADDON_SUPPORT_URL",
            "https://github.com/dcsubie/RTL433-Acurite-Bridge",
        ),
    )
