from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, liveness, readiness, SampleView, BulkUploadView

app_name = 'hierarchy'

router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset')

urlpatterns = [
    # Bulk upload endpoint must come before router to avoid 405
    path('assets/bulk/', BulkUploadView.as_view(), name='asset-bulk'),

    # Router URLs
    path('', include(router.urls)),

    # Health check endpoints
    path('health/liveness/', liveness, name='liveness'),
    path('health/readiness/', readiness, name='readiness'),

    # Sample view
    path('sample/', SampleView.as_view(), name='sample'),
]
