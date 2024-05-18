from opentelemetry import metrics, trace
import logging
import functools
from .logger import setup_file_logging, setup_syslog, setup_otlp_logging
from .otel import instrument_app, setup_otlp_span_exporter, setup_otlp_metric_exporter
from .helpers import signal_as_counter


class Observability:
    def __init__(self, app=None, **kwargs):
        self.metrics = {}
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, instrument=None, auto_instrument=True, otlp_export=None):
        logging.getLogger().setLevel(app.config.get("LOG_LEVEL", "DEBUG" if app.debug else "INFO"))

        if instrument is None:
            instrument = not getattr(app, "_is_instrumented_by_opentelemetry", False)
        instrument = app.config.get("OTEL_INSTRUMENT", instrument)
        otlp_export = app.config.get("OTLP_EXPORT", instrument and not app.debug if otlp_export is None else otlp_export)
        if instrument:
            instrument_app(app, auto_instrument=auto_instrument)

        if app.config.get("LOG_FILENAME"):
            setup_file_logging(app)
        if app.config.get("SYSLOG") or ("SYSLOG" not in app.config and not app.debug and app.config.get("SYSLOG_HOST")):
            setup_syslog(app)
        if app.config.get("OTLP_LOG"):
            setup_otlp_logging(app)
        if otlp_export:
            setup_otlp_span_exporter(app)
            setup_otlp_metric_exporter(app)

    @property
    def meter(self):
        return metrics.get_meter(self.app.config.get("OTEL_METER_NAME", self.app.import_name))

    @property
    def tracer(self):
        return trace.get_tracer(self.app.config.get("OTEL_TRACER_NAME", self.app.import_name))
    
    def create_counter(self, name, unit="", description=""):
        counter = self.meter.create_counter(name, unit, description)
        self.metrics[name] = counter
        return counter
    
    def counter(self, name):
        if name in self.metrics:
            return self.metrics[name]
        return self.create_counter(name)

    def signal_as_counter(self, signal, counter_name=None, **kwargs):
        if not counter:
            counter = self.counter(counter_name or signal.name)
        signal_as_counter(signal, counter, **kwargs)
    
    def create_gauge(self, name, unit="", description=""):
        gauge = self.meter.create_gauge(name, unit, description)
        self.metrics[name] = gauge
        return gauge
    
    def gauge(self, name):
        if name in self.metrics:
            return self.metrics[name]
        return self.create_gauge(name)
    
    def create_histogram(self, name, unit="", description=""):
        histo = self.meter.create_histogram(name, unit, description)
        self.metrics[name] = histo
        return histo
    
    def histogram(self, name):
        if name in self.metrics:
            return self.metrics[name]
        return self.create_histogram(name)
    
    def start_as_current_span(self, name, **kwargs):
        return self.tracer.start_as_current_span(name, **kwargs)
    
    def instrument(self, func=None, name=None, **span_kwargs):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(name or func.__name__, **span_kwargs):
                    return func(*args, **kwargs)
            return wrapper
        return decorator(func) if func else decorator