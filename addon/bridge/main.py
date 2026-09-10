"""
RTL433 MQTT Bridge main entry point.
"""

from __future__ import annotations

import json
import logging
import queue
import sys
import threading
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


def merge_state(
    previous: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Merge a partial packet into the last-known sensor state.

    Acurite 5n1-style stations alternate packet types (temp/humidity vs
    wind/rain). Publishing only the latest partial fields with retain=True
    would wipe earlier values from MQTT / Home Assistant.
    """

    merged = dict(previous or {})
    merged.update(payload)
    return merged


def process_message(
    message: dict,
    mqtt: MQTTBridge,
    discovery: DiscoveryPublisher,
    topic_root: str,
    whitelist: tuple[str, ...] = (),
    last_states: dict[str, dict[str, Any]] | None = None,
    seen_ids: set[str] | None = None,
) -> None:
    """Convert an rtl_433 JSON message into a SensorReading and publish it."""

    if "id" not in message:
        LOGGER.warning("Skipping rtl_433 message without a sensor id: %s", message)
        return

    sensor_id = str(message["id"])
    model = str(message.get("model", "Unknown"))

    # Log every packet (not only the first per id) so missing 5n1 traffic is obvious.
    LOGGER.info(
        "Packet id=%s model=%s keys=%s",
        sensor_id,
        model,
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
    payload = reading.to_dict()

    if last_states is not None:
        previous = last_states.get(sensor_id)
        if previous is None:
            LOGGER.info(
                "No retained/in-memory state for %s yet; publishing partial packet fields only until more arrive",
                sensor_id,
            )
        payload = merge_state(previous, payload)
        # Keep identity fields authoritative from the latest packet.
        payload["sensor_id"] = sensor_id
        payload["model"] = model
        last_states[sensor_id] = payload

    discovery_reading = SensorReading(
        sensor_id=sensor_id,
        model=str(payload.get("model", model)),
        temperature=payload.get("temperature"),
        humidity=payload.get("humidity"),
        wind_speed=payload.get("wind_speed"),
        wind_gust=payload.get("wind_gust"),
        wind_direction=payload.get("wind_direction"),
        rain_total=payload.get("rain_total"),
        pressure=payload.get("pressure"),
        battery_ok=payload.get("battery_ok"),
        rssi=payload.get("rssi"),
        snr=payload.get("snr"),
        noise=payload.get("noise"),
        channel=payload.get("channel"),
    )

    discovery.publish_available(discovery_reading)

    mqtt.publish_sensor(
        discovery_reading.base_topic(topic_root),
        payload,
        retain=True,
    )
    LOGGER.info(
        "Published %s (%s): %s",
        sensor_id,
        model,
        ",".join(
            sorted(
                key
                for key in payload.keys()
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

    last_states: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    # Drain rtl_433 stdout immediately so MQTT retained seeding cannot block
    # the pipe and overrun the SDR (weaker stations drop first).
    line_queue: queue.Queue[str | None] = queue.Queue()

    def _stdin_reader() -> None:
        try:
            for raw in sys.stdin:
                line_queue.put(raw)
        finally:
            line_queue.put(None)

    reader = threading.Thread(
        target=_stdin_reader,
        name="rtl433-stdin-reader",
        daemon=True,
    )
    reader.start()

    mqtt.seed_retained_states(config.mqtt_topic, last_states)

    try:
        while True:
            raw = line_queue.get()
            if raw is None:
                break

            line = raw.strip()
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
                    last_states=last_states,
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
