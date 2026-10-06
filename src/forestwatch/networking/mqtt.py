"""Minimal MQTT publisher/subscriber adapters."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from forestwatch.schemas.events import ForestEvent

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - handled by optional runtime dependency
    mqtt = None


@dataclass(frozen=True)
class MQTTConfig:
    host: str = "localhost"
    port: int = 1883
    topic_prefix: str = "forestwatch/events"
    keepalive: int = 30


def event_topic(config: MQTTConfig, event: ForestEvent) -> str:
    """Build an alert topic from the configured prefix and priority."""
    return f"{config.topic_prefix}/{event.priority.name.lower()}"


def event_payload(event: ForestEvent) -> str:
    """Serialize a ForestEvent as compact JSON."""
    return event.model_dump_json()


class MQTTPublisher:
    """Thin synchronous Paho publisher used by the demo."""

    def __init__(self, config: MQTTConfig) -> None:
        self.config = config
        self._client: Any | None = None

    def connect(self) -> None:
        """Connect to the broker."""
        if mqtt is None:
            raise RuntimeError("paho-mqtt is required for MQTT publishing")
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.connect(self.config.host, self.config.port, self.config.keepalive)

    def publish(self, event: ForestEvent) -> None:
        """Publish one event with MQTT QoS 1."""
        if self._client is None:
            raise RuntimeError("publisher is not connected")
        self._client.publish(event_topic(self.config, event), event_payload(event), qos=1)

    def close(self) -> None:
        """Disconnect the broker connection if open."""
        if self._client is not None:
            self._client.disconnect()
            self._client = None


class MQTTSubscriber:
    """Small subscriber adapter for integration tests and the local demo."""

    def __init__(self, config: MQTTConfig, client_id: str) -> None:
        self.config = config
        self.client_id = client_id
        self.messages: list[dict[str, Any]] = []
        self._client: Any | None = None

    def connect(self) -> None:
        """Connect and subscribe to all ForestWatch alert priorities."""
        if mqtt is None:
            raise RuntimeError("paho-mqtt is required for MQTT subscription")
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        self._client.on_message = self._on_message
        self._client.connect(self.config.host, self.config.port, self.config.keepalive)
        self._client.subscribe(f"{self.config.topic_prefix}/#", qos=1)
        self._client.loop_start()

    def _on_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        payload = json.loads(message.payload.decode("utf-8"))
        self.messages.append(payload)

    def close(self) -> None:
        """Stop the network loop and disconnect."""
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
