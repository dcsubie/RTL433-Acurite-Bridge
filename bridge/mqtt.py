import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

LOGGER = logging.getLogger("rtl433-bridge.mqtt")


class MQTTBridge:
    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
    ):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        if username:
            self.client.username_pw_set(username, password)

        self.client.connect(host, port, 60)
        self.client.loop_start()

        LOGGER.info("Connected to MQTT broker %s:%s", host, port)

    def publish_sensor(
        self,
        topic: str,
        payload: dict[str, Any],
    ) -> None:
        self.client.publish(
            topic,
            json.dumps(payload),
            retain=False,
        )

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
