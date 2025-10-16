import csv
import io
import logging

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse, Http404

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
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Only return top-level organizations
        return Asset.objects.filter(asset_type='organization')

    def retrieve(self, request, *args, **kwargs):
        """Custom 404 message for organization lookup"""
        try:
            instance = self.get_object()  # filtered by queryset
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response(
                {
                    "success": False,
                    "status_code": 404,
                    "error": {"detail": "No organization is assigned to this id"},
                    "message": "Not Found — Resource not available",
                    "trace_id": None
                },
                status=404
            )

    @action(detail=True, methods=['get'], url_path='children')
    def children(self, request, pk=None):
        """
        Retrieve all descendants of an asset.
        Optional query param: ?asset_type=<type>
        Example:
            /api/assets/23/children/?asset_type=Building
        """
        try:
            parent = self.get_object()
        except Http404:
            return Response(
                {
                    "success": False,
                    "status_code": 404,
                    "error": {"detail": "No organization is assigned to this id"},
                    "message": "Not Found — Resource not available",
                    "trace_id": None
                },
                status=404
            )

        asset_type = request.query_params.get('asset_type', None)

        # Recursive function to get all descendants
        def get_all_descendants(asset):
            descendants = list(asset.children.all())
            for child in asset.children.all():
                descendants.extend(get_all_descendants(child))
            return descendants

        all_children = get_all_descendants(parent)

        if asset_type:
            all_children = [child for child in all_children if child.asset_type == asset_type]

        serializer = self.get_serializer(all_children, many=True)
        return Response(serializer.data)


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
    Handles bulk upload of assets via JSON or CSV files with proper parent-child hierarchy.
    """

    def post(self, request, *args, **kwargs):
        # ---------------- JSON Upload ----------------
        if request.content_type == 'application/json':
            data = request.data if isinstance(request.data, list) else request.data.get('assets', [])
            return self.handle_bulk_upload(data)

        # ---------------- CSV Upload ----------------
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        data = list(reader)

        # Convert empty strings to None
        for row in data:
            for k, v in row.items():
                if v == "":
                    row[k] = None

        return self.handle_bulk_upload(data)

    def handle_bulk_upload(self, data):
        """
        Handles bulk creation in order of hierarchy
        """
        created_assets = {}  # Maps asset_name -> Asset instance

        # First pass: create top-level assets (organization)
        top_level = [d for d in data if d.get('asset_type') == 'organization']
        for d in top_level:
            d['parent'] = None
            serializer = AssetSerializer(data=d)
            if serializer.is_valid():
                asset = serializer.save()
                created_assets[asset.asset_name] = asset
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Second pass: create child assets
        children = [d for d in data if d.get('asset_type') != 'organization']
        for d in children:
            parent_name = d.get('parent')  # parent should be asset_name now
            parent_asset = created_assets.get(parent_name)
            if not parent_asset:
                return Response(
                    {"error": f"Parent '{parent_name}' not found. Upload parents first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            d['parent'] = parent_asset.id
            serializer = AssetSerializer(data=d)
            if serializer.is_valid():
                asset = serializer.save()
                created_assets[asset.asset_name] = asset
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Bulk upload successful", "count": len(created_assets)},
            status=status.HTTP_201_CREATED
        )
