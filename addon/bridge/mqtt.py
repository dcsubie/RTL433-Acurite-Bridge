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
    ) -> None:
        # No callbacks are registered, so use the constructor shared by
        # paho-mqtt 1.x and 2.x.  CallbackAPIVersion was introduced in 2.x.
        self.client = mqtt.Client()

        if username:
            self.client.username_pw_set(username, password)

        try:
            self.client.connect(host, port, 60)
        except Exception as err:
            LOGGER.exception("Unable to connect to MQTT broker: %s", err)
            raise

        self.client.loop_start()

        LOGGER.info("Connected to MQTT broker %s:%s", host, port)

    def publish_sensor(
        self,
        topic: str,
        payload: dict[str, Any],
        retain: bool = False,
    ) -> None:
        result = self.client.publish(
            topic,
            json.dumps(payload),
            retain=retain,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.warning(
                "Failed to publish %s (rc=%s)",
                topic,
                result.rc,
            )
        else:
            LOGGER.debug("Published %s", topic)

    def publish_json(
        self,
        topic: str,
        payload: dict[str, Any],
        retain: bool = False,
    ) -> None:
        self.publish_sensor(topic, payload, retain)

    def publish_text(
        self,
        topic: str,
        payload: str,
        retain: bool = False,
    ) -> None:
        result = self.client.publish(
            topic,
            payload,
            retain=retain,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.warning(
                "Failed to publish %s (rc=%s)",
                topic,
                result.rc,
            )

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
