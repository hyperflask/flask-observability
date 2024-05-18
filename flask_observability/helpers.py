from opentelemetry import trace


def signal_as_counter(signal, counter, quantity=1, attrs=None, signal_kwargs_as_attrs=False, callback=None):
    def listener(sender, **kwargs):
        _quantity = quantity
        _attrs = attrs
        if signal_kwargs_as_attrs:
            _attrs = dict(attrs or {}, **kwargs)
        if callback:
            r = callback(sender, kwargs, _attrs)
            if isinstance(r, tuple):
                _quantity, _attrs = r
            else:
                _attrs = r
        counter.add(_quantity, _attrs)

    signal.connect(listener, weak=False)


def signal_as_span_event(signal, event_name=None, attrs=None, signal_kwargs_as_attrs=False, callback=None):
    def listener(sender, **kwargs):
        current_span = trace.get_current_span()
        _attrs = attrs
        if signal_kwargs_as_attrs:
            _attrs = dict(attrs or {}, **kwargs)
        if callback:
            _attrs = callback(sender, kwargs, _attrs)
        current_span.add_event(event_name or signal.name, _attrs)

    signal.connect(listener, weak=False)