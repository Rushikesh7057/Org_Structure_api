"""
WSGI config for new_api project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'new_api.settings')

# --- OpenTelemetry setup (safe version) ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Prevent reinitialization on Django reload
if not isinstance(trace.get_tracer_provider(), TracerProvider):
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4318/v1/traces",
    )

    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

# --- End OpenTelemetry setup ---

application = get_wsgi_application()
