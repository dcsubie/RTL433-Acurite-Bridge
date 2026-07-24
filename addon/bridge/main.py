"""
RTL433 MQTT Bridge main entry point.
"""

import json
import logging
import sys

from config import load_config
from discovery import DiscoveryPublisher
from mqtt import MQTTBridge
from sensors import SensorReading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOGGER = logging.getLogger("rtl433-bridge")


def process_message(
    message: dict,
    mqtt: MQTTBridge,
    discovery: DiscoveryPublisher,
    topic_root: str,
    whitelist: tuple[str, ...] = (),
) -> None:
    """Convert an rtl_433 JSON message into a SensorReading and publish it."""

    if "id" not in message:
        LOGGER.warning("Skipping rtl_433 message without a sensor id: %s", message)
        return

    sensor_id = str(message["id"])

    if whitelist and sensor_id not in whitelist:
        LOGGER.debug("Skipping sensor %s because it is not whitelisted", sensor_id)
        return
    model = message.get("model", "Unknown")

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
        channel=str(message["channel"]) if "channel" in message else None,
    )

    # Publish Home Assistant discovery for values not previously announced.
    discovery.publish_available(reading)

    # Publish sensor state
    mqtt.publish_sensor(
        reading.base_topic(topic_root),
        reading.to_dict(),
    )


def main() -> None:
    """Main application loop."""

    config = load_config()

    mqtt = MQTTBridge(
        config.mqtt_host,
        config.mqtt_port,
        config.mqtt_username,
        config.mqtt_password,
    )

    discovery = DiscoveryPublisher(
        mqtt,
        config.mqtt_topic,
    )

    LOGGER.info("RTL433 Acurite Bridge started")

    try:
        for line in sys.stdin:
            line = line.strip()

            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                LOGGER.warning("Skipping invalid JSON: %s", line)
                continue

            try:
                process_message(
                    message,
                    mqtt,
                    discovery,
                    config.mqtt_topic,
                    config.whitelist,
                )
            except Exception:
                LOGGER.exception("Error processing rtl_433 message")

    except KeyboardInterrupt:
        LOGGER.info("Stopping bridge...")

    finally:
        mqtt.stop()


if __name__ == "__main__":
    main()
