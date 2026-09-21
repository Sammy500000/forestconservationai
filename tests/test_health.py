from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from forestwatch.app import HealthHandler


def test_health_endpoint() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{server.server_port}/healthz",
            timeout=2,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert response.status == 200
        assert payload["status"] == "ok"
        assert payload["service"] == "forestwatch"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
