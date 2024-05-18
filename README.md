# Flask-Observability

Make your Flask app observable using [OpenTelemetry](https://opentelemetry.io/), logging and more.

 - Auto instrument your app with OpenTelemetry
 - Export spans and metrics via OTLP automatically
 - Export logs in files or via [Syslog]() and OTLP
 - Utilities to use signals as counters and span events

## Installation

    pip install flask-observability

## Usage

```python
from flask import app
from flask_observability import Observability

app = Flask(__name__)
obs = Observability(app)
```

> [!IMPORTANT]
> Activate this extension before any other extensions

> [!IMPORTANT]
> No need to use the opentelemetry-instrument binary. (But if you do use it, instrumentation will not be performed by the extension)

> [!NOTE]
> The OTLP endpoint defaults to "localhost" so it's easy to use [OpenTelemetry Collector]() locally and forward to remote services from the collector

> [!WARNING]
> If app.debug is False, the OTLP exporter is enabled by default

## Metrics

Easily get a metric object:

```python
obs.counter("my-counter").add(1)
obs.gauge("my-gauge")
obs.histogram("my-histo")
```

Use a signal as a counter:

```python
from blinker import signal

account_created = signal("account-created")
obs.signal_as_counter(account_created)

account_created.send()
```

## Configuration

### Logging

| Config key | Description | Default |
| --- | --- | --- |
| LOG_LEVEL | Level for the root logger | DEBUG if app.debug else INFO |
| LOG_FILENAME | Write logs from all loggers in a file |
| SYSLOG | Whether to enable Syslog | True if SYSLOG_HOST is set manually and not in debug mode, False otherwise |
| SYSLOG_HOST |  | localhost |
| SYSLOG_PORT |  | 514 |
| SYSLOG_FACILITY |  | local0 |
| OTLP_LOG | Whether to enable sending logs via OTLP | False |

### Instrumentation

| Config key | Description | Default |
| --- | --- | --- |
| OTEL_INSTRUMENT | Whether to instrument the Flask app | True unless using opentelemetry-instrument |
| OTEL_AUTO_INSTRUMENT | Whether to auto initialize installed instrumentors (if OTEL_INSTRUMENT is true) | True |
| OTEL_DISABLE_AUTO_INSTRUMENTATIONS | Auto instrumentors to disable | [] |
| OTEL_INSTRUMENTORS | Import names or instrumentor classes to initialize | [] |
| OTLP_EXPORT | Whether to export span and metric using OTLP | OTEL_INSTRUMENT and not app.debug

### OTLP exporters

| Config key | Description | Default |
| --- | --- | --- |
| OTLP_ENDPOINT |  | localhost:4317 |
| OTLP_EXPORTER_OPTIONS | Keywords args that will be applied to ALL OTLP exporters used | {} |
| OTLP_SPAN_ENDPOINT | Specific endpoint for the span exporter | OTLP_ENDPOINT
| OTLP_SPAN_EXPORTER_OPTIONS | Keyword args for the span exporter | {} |
| OTLP_METRIC_ENDPOINT | Specific endpoint for the metric exporter | OTLP_ENDPOINT
| OTLP_METRIC_EXPORTER_OPTIONS | Keyword args for the metric exporter | {} |
| OTLP_LOG_ENDPOINT | Specific endpoint for the log exporter | OTLP_ENDPOINT
| OTLP_LOG_EXPORTER_OPTIONS | Keyword args for the log exporter | {} |

### Misc

| Config key | Description | Default |
| --- | --- | --- |
| OTEL_SERVICE_NAME | Name of the service to use in the resource definition | app.import_name
| OTEL_RESOURCE_ATTRIBUTES | A dict of attributes for the resource (may override service name) | {} 
| OTEL_TRACER_NAME | Name of the default tracer | app.import_name
| OTEL_METER_NAME | Name of the default meter | app.import_name