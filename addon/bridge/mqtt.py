import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

LOGGER = logging.getLogger("rtl433-bridge.mqtt")

PAYLOAD_AVAILABLE = "online"
PAYLOAD_NOT_AVAILABLE = "offline"


class MQTTBridge:
    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        availability_topic: str | None = None,
    ) -> None:
        # No callbacks are registered, so use the constructor shared by
        # paho-mqtt 1.x and 2.x.  CallbackAPIVersion was introduced in 2.x.
        self.client = mqtt.Client()
        self.availability_topic = availability_topic

        if username:
            self.client.username_pw_set(username, password)

        if self.availability_topic:
            # Broker publishes offline if the bridge disconnects uncleanly.
            self.client.will_set(
                self.availability_topic,
                PAYLOAD_NOT_AVAILABLE,
                qos=1,
                retain=True,
            )

        try:
            self.client.connect(host, port, 60)
        except Exception as err:
            LOGGER.exception("Unable to connect to MQTT broker: %s", err)
            raise

        self.client.loop_start()
        self.publish_availability(available=True)

        LOGGER.info("Connected to MQTT broker %s:%s", host, port)

    def publish_availability(self, available: bool) -> None:
        """Publish bridge online/offline status for Home Assistant."""
        if not self.availability_topic:
            return

        payload = PAYLOAD_AVAILABLE if available else PAYLOAD_NOT_AVAILABLE
        result = self.client.publish(
            self.availability_topic,
            payload,
            qos=1,
            retain=True,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.warning(
                "Failed to publish availability %s (rc=%s)",
                self.availability_topic,
                result.rc,
            )

    def publish_sensor(
        self,
        topic: str,
        payload: dict[str, Any],
        retain: bool = True,
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
        try:
            self.publish_availability(available=False)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
