from __future__ import annotations

import asyncio
import json
from dataclasses import asdict

from forestwatch.networking.demo import run_demo


def main() -> int:
    result = asyncio.run(run_demo())
    metrics = result["metrics"]
    payload = {
        "ordered_priorities": result["ordered_priorities"],
        "deliveries": result["deliveries"],
        "metrics": asdict(metrics),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
