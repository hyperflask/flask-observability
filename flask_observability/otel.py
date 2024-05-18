from opentelemetry.instrumentation.distro import DefaultDistro
from opentelemetry.instrumentation.auto_instrumentation._load import _load_instrumentors
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.environment_variables import OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from importlib import import_module
import inspect
import os


def instrument_app(app, instrumentors=None, auto_instrument=True, disable_auto_instrumentations=None):
    FlaskInstrumentor().instrument_app(app)

    disable_auto_instrumentations = app.config.get("OTEL_DISABLE_AUTO_INSTRUMENTATIONS", disable_auto_instrumentations)
    if app.config.get("OTEL_AUTO_INSTRUMENT", auto_instrument):
        disabled_impl = os.environ.get(OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, [])
        if isinstance(disabled_impl, str):
            disabled_impl = [p.strip() for p in disabled_impl.split(",")]
        disabled_impl.append("flask")
        if disable_auto_instrumentations:
            disabled_impl.extend(disable_auto_instrumentations)
        _load_instrumentors(DefaultDistro())

    instrumentors = app.config.get("OTEL_INSTRUMENTORS", instrumentors or [])
    for instrumentor in instrumentors:
        _load_instrumentor(instrumentor).instrument()


def setup_otlp_span_exporter(app, resource=None, **exporter_kwargs):
    if not resource:
        resource = _create_resource(app)

    endpoint = app.config.get("OTLP_SPAN_ENDPOINT", app.config.get("OTLP_ENDPOINT", exporter_kwargs.pop("endpoint", "localhost:4317")))
    exporter_kwargs.update(app.config.get("OTLP_EXPORTER_OPTIONS", {}))
    exporter_kwargs.update(app.config.get("OTLP_SPAN_EXPORTER_OPTIONS", {}))
    exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", **exporter_kwargs)

    traceProvider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(exporter)
    traceProvider.add_span_processor(processor)
    trace.set_tracer_provider(traceProvider)


def setup_otlp_metric_exporter(app, resource=None, **exporter_kwargs):
    if not resource:
        resource = _create_resource(app)
        
    endpoint = app.config.get("OTLP_METRIC_ENDPOINT", app.config.get("OTLP_ENDPOINT", exporter_kwargs.pop("endpoint", "localhost:4317")))
    exporter_kwargs.update(app.config.get("OTLP_EXPORTER_OPTIONS", {}))
    exporter_kwargs.update(app.config.get("OTLP_METRIC_EXPORTER_OPTIONS", {}))
    exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics", **exporter_kwargs)

    reader = PeriodicExportingMetricReader(exporter)
    meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meterProvider)


def _create_resource(app):
    if not resource:
        resource = app.config.get("OTEL_RESOURCE")
    if not resource:
        attrs = app.config.get("OTEL_RESOURCE_ATTRIBUTES")
        attrs.setdefault(SERVICE_NAME, app.config.get("OTEL_SERVICE_NAME", app.import_name))
        resource = Resource(attributes=attrs)
        if "OTEL_RESOURCE" not in app.config:
            app.config["OTEL_RESOURCE"] = resource
    return resource


def _load_instrumentor(instrumentor):
    if not isinstance(instrumentor, str):
        if inspect.isclass(instrumentor):
            return instrumentor()
        return instrumentor
    
    try:
        m = import_module(f"opentelemetry.instrumentation.{instrumentor}")
    except ImportError:
        m = import_module(instrumentor)

    for cls in m.__dict__.values():
        if inspect.isclass(cls) and issubclass(cls, BaseInstrumentor):
            return cls()
        
    raise ImportError(f"OpenTelemetry instrumentor '{instrumentor}' not found")