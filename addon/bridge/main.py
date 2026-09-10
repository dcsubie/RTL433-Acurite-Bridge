"""
RTL433 MQTT Bridge main entry point.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from config import load_config
from discovery import DiscoveryPublisher
from mqtt import MQTTBridge
from sensors import SensorReading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOGGER = logging.getLogger("rtl433-bridge")


def _rf_summary(message: dict[str, Any]) -> str:
    """Format optional RF diagnostic fields for log lines."""

    parts: list[str] = []
    for key in ("rssi", "snr", "noise", "freq"):
        if key in message and message[key] is not None:
            parts.append(f"{key}={message[key]}")
    return f" ({', '.join(parts)})" if parts else ""


def reading_from_message(message: dict[str, Any]) -> SensorReading:
    """Normalize an rtl_433 JSON object into a SensorReading."""

    sensor_id = str(message["id"])
    model = str(message.get("model", "Unknown"))

    return SensorReading(
        sensor_id=sensor_id,
        model=model,
        temperature=message.get("temperature_C", message.get("temperature_F")),
        humidity=message.get("humidity"),
        wind_speed=message.get("wind_avg_km_h", message.get("wind_avg_m_s")),
        wind_gust=message.get("wind_max_km_h", message.get("wind_max_m_s")),
        wind_direction=message.get("wind_dir_deg"),
        rain_total=message.get("rain_mm", message.get("rain_in")),
        pressure=message.get("pressure_hPa", message.get("pressure_PSI")),
        battery_ok=message.get("battery_ok"),
        rssi=message.get("rssi"),
        snr=message.get("snr"),
        noise=message.get("noise"),
        channel=str(message["channel"]) if "channel" in message else None,
    )


def process_message(
    message: dict,
    mqtt: MQTTBridge,
    discovery: DiscoveryPublisher,
    topic_root: str,
    whitelist: tuple[str, ...] = (),
    seen_ids: set[str] | None = None,
) -> None:
    """Convert an rtl_433 JSON message into a SensorReading and publish it."""

    if "id" not in message:
        LOGGER.warning(
            "Skipping rtl_433 message without a sensor id: model=%s keys=%s",
            message.get("model", "Unknown"),
            ",".join(sorted(message.keys())),
        )
        return

    sensor_id = str(message["id"])
    model = str(message.get("model", "Unknown"))

    # Always log every decoded packet so missing 5n1 traffic is obvious.
    LOGGER.info(
        "Packet id=%s model=%s%s keys=%s",
        sensor_id,
        model,
        _rf_summary(message),
        ",".join(sorted(message.keys())),
    )

    if seen_ids is not None and sensor_id not in seen_ids:
        seen_ids.add(sensor_id)
        LOGGER.info(
            "Heard sensor id=%s model=%s (first time this run)",
            sensor_id,
            model,
        )

    if whitelist and sensor_id not in whitelist:
        LOGGER.info(
            "Skipping sensor %s (not in whitelist: %s)",
            sensor_id,
            ",".join(whitelist),
        )
        return

    reading = reading_from_message(message)

    discovery.publish_available(reading)

    mqtt.publish_sensor(
        reading.base_topic(topic_root),
        reading.to_dict(),
        retain=True,
    )
    LOGGER.info(
        "Published %s (%s): %s",
        sensor_id,
        model,
        ",".join(
            sorted(
                key
                for key in reading.to_dict().keys()
                if key not in {"sensor_id", "model", "channel"}
            )
        ),
    )


def main() -> None:
    """Main application loop."""

    config = load_config()

    mqtt = MQTTBridge(
        config.mqtt_host,
        config.mqtt_port,
        config.mqtt_username,
        config.mqtt_password,
        availability_topic=config.availability_topic,
    )

    discovery = DiscoveryPublisher(
        mqtt,
        config.mqtt_topic,
        availability_topic=config.availability_topic,
        origin_name=config.addon_name,
        origin_version=config.addon_version,
        origin_support_url=config.addon_support_url,
    )

    LOGGER.info(
        "RTL433 Acurite Bridge started (v%s)",
        config.addon_version,
    )
    if config.whitelist:
        LOGGER.info("Active whitelist: %s", ",".join(config.whitelist))
    else:
        LOGGER.info("Active whitelist: None (accepting all sensor IDs)")

    seen_ids: set[str] = set()

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
                    seen_ids=seen_ids,
                )
            except Exception:
                LOGGER.exception("Error processing rtl_433 message")

    except KeyboardInterrupt:
        LOGGER.info("Stopping bridge...")

    finally:
        mqtt.stop()


if __name__ == "__main__":
    main()
