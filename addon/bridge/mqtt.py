import json
import logging
import threading
import time
from typing import Any, Callable

import paho.mqtt.client as mqtt

LOGGER = logging.getLogger("rtl433-bridge.mqtt")

PAYLOAD_AVAILABLE = "online"
PAYLOAD_NOT_AVAILABLE = "offline"

# Startup connect retry: grow from 1s toward 60s while Mosquitto comes up.
CONNECT_RETRY_INITIAL_SECONDS = 1
CONNECT_RETRY_MAX_SECONDS = 60

# Runtime reconnect backoff used by paho after an unexpected disconnect.
RECONNECT_MIN_SECONDS = 1
RECONNECT_MAX_SECONDS = 120


def _create_client() -> mqtt.Client:
    """Create a paho client compatible with 1.x and 2.x."""

    # Prefer VERSION1 callbacks so on_connect works on paho 2.x while staying
    # compatible with Alpine's older py3-paho-mqtt package.
    try:
        return mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except AttributeError:
        pass

    try:
        from paho.mqtt.enums import CallbackAPIVersion

        return mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION1)
    except (ImportError, AttributeError, TypeError):
        return mqtt.Client()


class MQTTBridge:
    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        availability_topic: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.availability_topic = availability_topic
        self._stopping = False

        self.client = _create_client()
        self.client.reconnect_delay_set(
            min_delay=RECONNECT_MIN_SECONDS,
            max_delay=RECONNECT_MAX_SECONDS,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

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

        self._connect_with_retry()
        self.client.loop_start()

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict[str, Any],
        rc: int,
        properties: Any = None,
    ) -> None:
        if rc != 0:
            LOGGER.warning("MQTT connect acknowledged with rc=%s", rc)
            return

        LOGGER.info("Connected to MQTT broker %s:%s", self.host, self.port)
        self.publish_availability(available=True)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
        properties: Any = None,
    ) -> None:
        if self._stopping:
            LOGGER.info("Disconnected from MQTT broker")
            return

        if rc == 0:
            LOGGER.info("Disconnected from MQTT broker")
        else:
            LOGGER.warning(
                "Unexpected MQTT disconnect (rc=%s); paho will retry with backoff",
                rc,
            )

    def _connect_with_retry(self) -> None:
        """Block until the broker accepts a connection."""

        delay = CONNECT_RETRY_INITIAL_SECONDS
        attempt = 1

        while True:
            try:
                self.client.connect(self.host, self.port, 60)
                LOGGER.info(
                    "MQTT broker %s:%s accepted connection (attempt %s)",
                    self.host,
                    self.port,
                    attempt,
                )
                return
            except Exception as err:
                LOGGER.warning(
                    "MQTT connect attempt %s to %s:%s failed: %s; retrying in %ss",
                    attempt,
                    self.host,
                    self.port,
                    err,
                    delay,
                )
                time.sleep(delay)
                attempt += 1
                delay = min(delay * 2, CONNECT_RETRY_MAX_SECONDS)

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

    def seed_retained_states(
        self,
        topic_root: str,
        last_states: dict[str, dict[str, Any]],
        timeout: float = 2.0,
    ) -> int:
        """Load retained sensor JSON into last_states before processing packets.

        Acurite 5n1-style stations send partial packets. Without seeding, the
        first post-restart publish would overwrite a full retained payload with
        a partial one and wipe temperature/humidity in Home Assistant.
        """

        pattern = f"{topic_root}/+"
        loaded = 0
        lock = threading.Lock()

        def on_message(
            client: mqtt.Client,
            userdata: Any,
            msg: mqtt.MQTTMessage,
        ) -> None:
            nonlocal loaded
            if not msg.payload:
                return

            topic = msg.topic
            if not topic.startswith(f"{topic_root}/"):
                return

            sensor_id = topic[len(topic_root) + 1 :]
            if "/" in sensor_id or sensor_id in {"", "bridge"}:
                return

            try:
                data = json.loads(msg.payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                LOGGER.warning("Ignoring invalid retained payload on %s", topic)
                return

            if not isinstance(data, dict):
                return

            with lock:
                last_states[sensor_id] = data
                loaded += 1

        previous_handler: Callable[..., Any] | None = self.client.on_message
        self.client.on_message = on_message
        subscribe_result = self.client.subscribe(pattern, qos=1)
        result = (
            subscribe_result[0]
            if isinstance(subscribe_result, tuple)
            else subscribe_result
        )
        if result != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.warning("Failed to subscribe for retained seed (%s)", result)
            self.client.on_message = previous_handler
            return 0

        # Retained messages are delivered immediately on subscribe; wait briefly
        # for the broker to flush them before unsubscribing.
        time.sleep(timeout)

        self.client.unsubscribe(pattern)
        self.client.on_message = previous_handler

        LOGGER.info(
            "Seeded %s retained sensor state(s) from MQTT topic %s",
            loaded,
            pattern,
        )
        return loaded

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
        self._stopping = True
        try:
            self.publish_availability(available=False)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
