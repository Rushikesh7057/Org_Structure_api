from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Asset Management API",
        default_version='v1',
        description="API documentation for managing organizational assets and their details.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@nexgensis.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
