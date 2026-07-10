from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator
from urllib.parse import unquote

from app.config import settings

logger = logging.getLogger(__name__)

_configured = False
_otel_available = True
_counters: dict[str, Any] = {}
_histograms: dict[str, Any] = {}

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as OTLPGrpcMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as OTLPHttpMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHttpSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
except Exception:  # pragma: no cover - optional dependency guard
    _otel_available = False


def configure_observability() -> bool:
    global _configured
    if _configured:
        return True
    if not settings.OBSERVABILITY_ENABLED:
        return False
    if not _otel_available:
        logger.warning("OpenTelemetry packages are not available; observability disabled")
        return False

    try:
        resource = Resource.create(
            {
                SERVICE_NAME: settings.OTEL_SERVICE_NAME,
                DEPLOYMENT_ENVIRONMENT: settings.OTEL_DEPLOYMENT_ENVIRONMENT,
            }
        )
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = _build_span_exporter()
        if span_exporter is not None:
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)

        metric_exporter = _build_metric_exporter()
        if metric_exporter is not None:
            metric_reader = PeriodicExportingMetricReader(metric_exporter)
            metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

        _configured = True
        logger.info("OpenTelemetry observability configured exporter=%s", settings.OBSERVABILITY_EXPORTER)
        return True
    except Exception as exc:  # pragma: no cover - telemetry must never break app startup
        logger.warning("OpenTelemetry observability setup failed: %s", exc)
        return False


def _build_span_exporter():
    if settings.OBSERVABILITY_EXPORTER == "console":
        return ConsoleSpanExporter()
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info("OTLP endpoint not configured; traces will not be exported")
        return None
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        return OTLPGrpcSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=_parse_otlp_headers(),
        )
    return OTLPHttpSpanExporter(
        endpoint=_signal_endpoint("/v1/traces"),
        headers=_parse_otlp_headers(),
    )


def _build_metric_exporter():
    if settings.OBSERVABILITY_EXPORTER == "console":
        return ConsoleMetricExporter()
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info("OTLP endpoint not configured; metrics will not be exported")
        return None
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        return OTLPGrpcMetricExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=_parse_otlp_headers(),
        )
    return OTLPHttpMetricExporter(
        endpoint=_signal_endpoint("/v1/metrics"),
        headers=_parse_otlp_headers(),
    )


def _signal_endpoint(path: str) -> str:
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    if endpoint.endswith(path):
        return endpoint
    return f"{endpoint}{path}"


def _parse_otlp_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in settings.OTEL_EXPORTER_OTLP_HEADERS.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = unquote(value.strip())
        if key:
            headers[key] = value
    return headers


def telemetry_enabled() -> bool:
    return bool(settings.OBSERVABILITY_ENABLED and _otel_available)


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any | None]:
    if not telemetry_enabled():
        yield None
        return
    configure_observability()
    tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            if value is not None:
                span.set_attribute(key, value)
        yield span


def increment_counter(name: str, value: int = 1, attributes: dict[str, Any] | None = None) -> None:
    if not telemetry_enabled():
        return
    try:
        configure_observability()
        counter = _counters.get(name)
        if counter is None:
            counter = metrics.get_meter(settings.OTEL_SERVICE_NAME).create_counter(name)
            _counters[name] = counter
        counter.add(value, attributes=_clean_attributes(attributes))
    except Exception as exc:  # pragma: no cover
        logger.debug("counter_record_failed name=%s error=%s", name, exc)


def record_histogram(name: str, value: float, attributes: dict[str, Any] | None = None) -> None:
    if not telemetry_enabled():
        return
    try:
        configure_observability()
        histogram = _histograms.get(name)
        if histogram is None:
            histogram = metrics.get_meter(settings.OTEL_SERVICE_NAME).create_histogram(name)
            _histograms[name] = histogram
        histogram.record(value, attributes=_clean_attributes(attributes))
    except Exception as exc:  # pragma: no cover
        logger.debug("histogram_record_failed name=%s error=%s", name, exc)


def _clean_attributes(attributes: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in (attributes or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
