
from django.contrib import admin
from django.urls import path, include
from .swagger import schema_view
from hierarchy.views import home

urlpatterns = [
    # Home page
    path('', home, name='home'),

    # Django admin
    path('admin/', admin.site.urls),

    # Hierarchy app (plug-and-play)
    path('api/', include('hierarchy.urls', namespace='hierarchy')),

    # API documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
