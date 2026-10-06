"""Network experiment metrics."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class DeliverySample:
    """One measured delivery duration in milliseconds."""

    priority: int
    latency_ms: float
    delivered: bool = True


@dataclass(frozen=True)
class NetworkMetrics:
    """Aggregate routing and delivery metrics."""

    sample_count: int
    delivery_rate: float
    mean_latency_ms: float
    critical_mean_latency_ms: float | None


def calculate_metrics(samples: list[DeliverySample]) -> NetworkMetrics:
    """Calculate compact metrics for the networking experiment."""
    if not samples:
        return NetworkMetrics(0, 0.0, 0.0, None)

    delivered = [sample for sample in samples if sample.delivered]
    critical = [sample.latency_ms for sample in delivered if sample.priority == 0]
    return NetworkMetrics(
        sample_count=len(samples),
        delivery_rate=len(delivered) / len(samples),
        mean_latency_ms=mean(sample.latency_ms for sample in delivered) if delivered else 0.0,
        critical_mean_latency_ms=mean(critical) if critical else None,
    )
