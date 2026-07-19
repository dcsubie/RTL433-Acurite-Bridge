#!/usr/bin/env python3

import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOGGER = logging.getLogger("rtl433-bridge")


def process_message(message: dict) -> None:
    """Process a single rtl_433 JSON message."""
    model = message.get("model", "Unknown")
    sensor_id = message.get("id", "Unknown")

    LOGGER.info(
        "Received message from %s (ID: %s)",
        model,
        sensor_id,
    )

    # MQTT publishing will be added in the next step.
    LOGGER.debug(json.dumps(message))


def main() -> int:
    LOGGER.info("RTL433 Acurite Bridge starting...")

    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        try:
            message = json.loads(line)
            process_message(message)
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON: %s", line)

    LOGGER.info("Bridge stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
