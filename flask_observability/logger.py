import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from .otel import _create_resource


def setup_file_logging(app, filename=None, logger=None):
    if not logger:
        logger = logging.getLogger()
    filename = app.config.get("LOG_FILENAME", filename or "app-log.txt")
    logger.addHandler(logging.FileHandler(filename))


def setup_syslog(app, host=None, port=None, facility=None, logger=None):
    if not logger:
        logger = logging.getLogger()
    host = app.config.get("SYSLOG_HOST", host or "localhost")
    port = app.config.get("SYSLOG_PORT", port or 514)
    facility = app.config.get("SYSLOG_FACILITY", facility or "local0")
    syslog_handler = logging.handlers.SysLogHandler(address=(host, port), facility=facility)
    logger.addHandler(syslog_handler)
    return syslog_handler


def setup_otlp_logging(app, resource=None, logger=None, **exporter_kwargs):
    if not resource:
        resource = _create_resource(app)
    if not logger:
        logger = logging.getLogger()

    LoggingInstrumentor().instrument(set_logging_format=True)

    endpoint = app.config.get("OTLP_LOG_ENDPOINT", app.config.get("OTLP_ENDPOINT", exporter_kwargs.pop("endpoint", "localhost:4317")))
    exporter_kwargs.update(app.config.get("OTLP_EXPORTER_OPTIONS", {}))
    exporter_kwargs.update(app.config.get("OTLP_LOG_EXPORTER_OPTIONS", {}))
    exporter = OTLPLogExporter(endpoint=endpoint, **exporter_kwargs)

    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logger.getEffectiveLevel(), logger_provider=logger_provider)
    logger.addHandler(handler)
    return logger_provider