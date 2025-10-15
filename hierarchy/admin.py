# hierarchy/admin.py
from django.contrib import admin
from .models import Asset, AssetDetail

class AssetDetailInline(admin.StackedInline):
    model = AssetDetail
    extra = 0

class AssetAdmin(admin.ModelAdmin):
    inlines = [AssetDetailInline]
    list_display = (
        'asset_name', 'asset_type', 'parent', 'is_active', 'start_date', 'end_date', 'hierarchy_level',
        'get_location', 'get_building', 'get_floor', 'get_room', 'get_line'
    )
    list_filter = ('asset_type', 'is_active')
    search_fields = ('asset_name', 'description')

    # Methods to show related AssetDetail fields
    def get_location(self, obj):
        return obj.details.location if hasattr(obj, 'details') and obj.details else '-'
    get_location.short_description = 'Location'

    def get_building(self, obj):
        return obj.details.building if hasattr(obj, 'details') and obj.details else '-'
    get_building.short_description = 'Building'

    def get_floor(self, obj):
        return obj.details.floor if hasattr(obj, 'details') and obj.details else '-'
    get_floor.short_description = 'Floor'

    def get_room(self, obj):
        return obj.details.room if hasattr(obj, 'details') and obj.details else '-'
    get_room.short_description = 'Room'

    def get_line(self, obj):
        return obj.details.line if hasattr(obj, 'details') and obj.details else '-'
    get_line.short_description = 'Line'

admin.site.register(Asset, AssetAdmin)
