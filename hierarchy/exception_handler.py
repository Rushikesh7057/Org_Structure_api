import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from opentelemetry.trace import get_current_span

# Create a logger for this module
logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler with logging, trace ID, and user info.
    """
    # Standard DRF response
    response = exception_handler(exc, context)

    # Get view and request
    view = context.get('view', None)
    request = context.get('request', None)
    view_name = view.__class__.__name__ if view else 'UnknownView'
    user = getattr(request, 'user', None)
    username = user.username if user and user.is_authenticated else 'anonymous'

    # Get current OpenTelemetry span
    span = get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x') if span else 'N/A'
    span_id = format(span.get_span_context().span_id, '016x') if span else 'N/A'

    if response is not None:
        # Log warning-level handled errors
        logger.warning(
            f"[{view_name}] User={username} TraceID={trace_id} SpanID={span_id} "
            f"Handled exception: {exc} — Status: {response.status_code}"
        )

        custom_response = {
            "success": False,
            "status_code": response.status_code,
            "error": response.data,
            "message": get_error_message(response.status_code),
            "trace_id": trace_id
        }
        return Response(custom_response, status=response.status_code)

    # Log critical unhandled exceptions
    logger.error(
        f"[{view_name}] User={username} TraceID={trace_id} SpanID={span_id} "
        f"Unhandled exception: {exc}",
        exc_info=True
    )

    return Response({
        "success": False,
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error": str(exc),
        "message": "Internal server error",
        "trace_id": trace_id
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_error_message(status_code):
    messages = {
        400: "Bad Request — Invalid data or parameters",
        401: "Unauthorized — Please log in",
        403: "Forbidden — Access denied",
        404: "Not Found — Resource not available",
        405: "Method Not Allowed — Invalid HTTP method",
        500: "Internal Server Error — Something went wrong"
    }
    return messages.get(status_code, "An unexpected error occurred")
