# hierarchy/views.py

import csv
import io
import logging

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from opentelemetry import trace

from .models import Asset
from .serializers import AssetSerializer
from .permissions import IsOwnerOrReadOnly

# Logger and Tracer
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# -------------------- Asset ViewSet --------------------
class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    @action(detail=True, methods=['get'], url_path='children')
    def get_children(self, request, pk=None):
        """
        Retrieve all child assets of a given asset.
        """
        with tracer.start_as_current_span("get_children") as span:
            trace_id = format(span.get_span_context().trace_id, '032x')
            try:
                with tracer.start_as_current_span("fetch_asset") as db_span:
                    asset = self.get_object()
                    db_span.set_attribute("asset.id", asset.id)
                    db_span.set_attribute("user.username", str(request.user))

                with tracer.start_as_current_span("fetch_children") as children_span:
                    children = asset.children.all()
                    children_span.set_attribute("children.count", len(children))

                serializer = self.get_serializer(children, many=True)
                logger.info(f"[trace_id={trace_id}] User {request.user} fetched children of Asset {asset.id}")
                return Response(serializer.data)

            except Asset.DoesNotExist:
                logger.warning(f"[trace_id={trace_id}] Asset {pk} not found for user {request.user}")
                return Response({"detail": f"Asset {pk} not found"}, status=404)
            except Exception as exc:
                logger.error(f"[trace_id={trace_id}] Error fetching children for Asset {pk}: {exc}", exc_info=True)
                return Response({"detail": "Internal server error"}, status=500)


# -------------------- Health Probes --------------------
def liveness(request):
    with tracer.start_as_current_span("liveness_probe") as span:
        trace_id = format(span.get_span_context().trace_id, '032x')
        logger.info(f"[trace_id={trace_id}] Liveness check")
        return JsonResponse({"status": "alive"})


def readiness(request):
    with tracer.start_as_current_span("readiness_probe") as span:
        trace_id = format(span.get_span_context().trace_id, '032x')
        db_conn = connections['default']
        try:
            with tracer.start_as_current_span("db_readiness_check"):
                db_conn.cursor()
            logger.info(f"[trace_id={trace_id}] Readiness check passed")
            return JsonResponse({"status": "ready"})
        except OperationalError:
            logger.warning(f"[trace_id={trace_id}] Readiness check failed")
            return JsonResponse({"status": "not ready"}, status=503)


# -------------------- Landing Page --------------------
def home(request):
    with tracer.start_as_current_span("home") as span:
        trace_id = format(span.get_span_context().trace_id, '032x')
        logger.info(f"[trace_id={trace_id}] Home page accessed")
        return JsonResponse({
            "message": "Welcome to the new_api application",
            "status": "alive",
            "api_docs": "/swagger/"
        })


# -------------------- Sample API --------------------
class SampleView(APIView):
    def get(self, request):
        with tracer.start_as_current_span("process_sample_request") as span:
            span.set_attribute("user.id", request.user.id if request.user.is_authenticated else "anonymous")
            span.set_attribute("request.path", request.path)

            result = {"message": "Hello, tracing world!"}
            span.add_event("Returning response", {"response_length": len(str(result))})

            return Response(result)


# -------------------- Bulk Upload API --------------------
class BulkUploadView(APIView):
    """
    Handles bulk upload of assets via JSON or CSV files.
    """

    def post(self, request, *args, **kwargs):
        # ---------------- JSON Upload ----------------
        if request.content_type == 'application/json':
            data = request.data if isinstance(request.data, list) else request.data.get('assets', [])
            serializer = AssetSerializer(data=data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Bulk upload successful", "count": len(serializer.data)}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ---------------- CSV Upload ----------------
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        assets = []

        for row in reader:
            asset_data = {
                "asset_name": row.get("asset_name"),
                "asset_type": row.get("asset_type"),
                "hierarchy_level": int(row.get("hierarchy_level", 0)),
                "parent": row.get("parent") or None,
                "description": row.get("description"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date") or None,
                "is_active": row.get("is_active", "True").lower() == "true",
                "details": {
                    "location": row.get("location") or "",
                    "building": row.get("building") or "",
                    "floor": row.get("floor"),
                    "room": row.get("room"),
                    "line": row.get("line"),
                }
            }
            assets.append(asset_data)

        serializer = AssetSerializer(data=assets, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Bulk upload successful", "count": len(serializer.data)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
