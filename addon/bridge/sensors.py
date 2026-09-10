"""
Sensor models for the RTL433 Acurite Bridge.
"""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SensorReading:
    """Represents a normalized reading from an rtl_433 sensor."""

    sensor_id: str
    model: str

    temperature: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    wind_gust: float | None = None
    wind_direction: int | None = None
    rain_total: float | None = None
    pressure: float | None = None

    battery_ok: bool | None = None
    rssi: float | None = None
    snr: float | None = None
    noise: float | None = None

    channel: str | None = None

    def device_name(self) -> str:
        """Return a friendly Home Assistant device name."""
        return f"{self.model} {self.sensor_id}"

    def manufacturer(self) -> str:
        """Return a manufacturer label based on the rtl_433 model string."""
        model = self.model.lower()
        if "acurite" in model:
            return "Acurite"
        if model in {"", "unknown"}:
            return "rtl_433"
        # Keep Acurite-first defaults, but don't mislabel other brands.
        return "rtl_433"

    def base_topic(self, root_topic: str) -> str:
        """Return the MQTT state topic."""
        return f"{root_topic}/{self.sensor_id}"

    def to_dict(self) -> dict[str, Any]:
        """Return the reading without None values."""

        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None
        }
