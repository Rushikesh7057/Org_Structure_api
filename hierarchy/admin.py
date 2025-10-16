from django.contrib import admin
from .models import Asset

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_name', 'asset_type', 'parent', 'is_active',
        'start_date', 'end_date', 'hierarchy_level'
    )
    list_filter = ('asset_type', 'is_active')
    search_fields = ('asset_name', 'description')
