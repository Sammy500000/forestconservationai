from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from forestwatch.logging import configure_logging
from forestwatch.schemas.events import ForestEvent

LOGGER = logging.getLogger("forestwatch.app")


class HealthHandler(BaseHTTPRequestHandler):
    server_version = "ForestWatchHealth/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/healthz":
            self._write_json(404, {"status": "not_found"})
            return

        self._write_json(
            200,
            {
                "status": "ok",
                "service": "forestwatch",
                "version": "0.1.0",
            },
        )

    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("http | " + format_string, *args)

    def _write_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    configure_logging()

    host = os.getenv("FORESTWATCH_APP_HOST", "127.0.0.1")
    port = int(os.getenv("FORESTWATCH_APP_PORT", "8500"))

    example = ForestEvent.example()
    LOGGER.info("phase 1 runtime initialized | example_event=%s", example.event_id)

    server = ThreadingHTTPServer((host, port), HealthHandler)
    LOGGER.info("health service listening on http://%s:%s/healthz", host, port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutdown requested")
    finally:
        server.server_close()

    return 0
