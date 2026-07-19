"""
Sensor models for the RTL433 Acurite Bridge.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SensorReading:
    """Represents a single reading from an rtl_433 sensor."""

    sensor_id: str
    model: str

    temperature: Optional[float] = None
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_gust: Optional[float] = None
    wind_direction: Optional[int] = None
    rain_total: Optional[float] = None
    pressure: Optional[float] = None

    battery_ok: Optional[bool] = None
    rssi: Optional[float] = None
    snr: Optional[float] = None
    noise: Optional[float] = None

    channel: Optional[str] = None

    def device_name(self) -> str:
        """Return a friendly device name."""
        return f"{self.model} {self.sensor_id}"

    def base_topic(self, root_topic: str) -> str:
        """Return the MQTT base topic."""
        return f"{root_topic}/{self.sensor_id}"

    def to_dict(self) -> dict:
        """Convert the reading to a dictionary, excluding None values."""

        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None
        }
