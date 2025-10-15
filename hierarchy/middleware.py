import uuid
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestTracingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Assign a unique trace ID for every request
        trace_id = str(uuid.uuid4())
        request.trace_id = trace_id
        request.start_time = time.time()

        logger.info(f"[TRACE {trace_id}] Incoming {request.method} {request.path}")
        return None

    def process_response(self, request, response):
        trace_id = getattr(request, "trace_id", "unknown")
        duration = time.time() - getattr(request, "start_time", time.time())

        logger.info(f"[TRACE {trace_id}] Completed {request.method} {request.path} in {duration:.3f}s — Status {response.status_code}")
        response["X-Trace-ID"] = trace_id  # Add trace ID to the response headers
        return response
