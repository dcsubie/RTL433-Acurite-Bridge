#!/usr/bin/env python3

import json
import logging
import sys

from config import load_config
from mqtt import MQTTBridge
from sensors import SensorReading
from discovery import DiscoveryPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOGGER = logging.getLogger("rtl433-bridge")


def process_message(message: dict, mqtt: MQTTBridge, topic_root: str) -> None:
    """Process a single rtl_433 JSON message."""

    model = message.get("model", "Unknown")
    sensor_id = str(message.get("id", "Unknown"))

    LOGGER.info("Received message from %s (ID: %s)", model, sensor_id)

    reading = SensorReading(
        sensor_id=sensor_id,
        model=model,
        temperature=message.get("temperature_C"),
        humidity=message.get("humidity"),
        wind_speed=message.get("wind_avg_km_h"),
        wind_gust=message.get("wind_max_km_h"),
        wind_direction=message.get("wind_dir_deg"),
        rain_total=message.get("rain_mm"),
        pressure=message.get("pressure_hPa"),
        battery_ok=message.get("battery_ok"),
        rssi=message.get("rssi"),
        snr=message.get("snr"),
        noise=message.get("noise"),
        channel=message.get("channel"),
    )

    topic = reading.base_topic(topic_root)

    mqtt.publish_sensor(
        topic,
        reading.to_dict(),
    )


def main() -> int:
    LOGGER.info("RTL433 Acurite Bridge starting...")

    config = load_config()

    mqtt = MQTTBridge(
        config.mqtt_host,
        config.mqtt_port,
        config.mqtt_username,
        config.mqtt_password,
    )

    try:
        for line in sys.stdin:
            line = line.strip()

            if not line:
                continue

            try:
                message = json.loads(line)
                process_message(
                    message,
                    mqtt,
                    config.mqtt_topic,
                )

            except json.JSONDecodeError:
                LOGGER.warning("Invalid JSON: %s", line)

    finally:
        mqtt.stop()

    LOGGER.info("Bridge stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
