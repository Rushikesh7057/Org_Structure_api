from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Asset(models.Model):
    ASSET_TYPES = [
        ('group', 'Group'),
        ('subgroup', 'Subgroup'),
        ('organization', 'Organization'),
        ('location', 'Location'),
        ('plant', 'Plant'),
        ('unit', 'Unit'),
        ('machine', 'Machine'),
        ('building', 'Building'),
        ('other', 'Other'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES, db_index=True)
    hierarchy_level = models.PositiveIntegerField(default=0, editable=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', db_index=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['asset_name']

    def clean(self):
        # Organization can be top-level
        if self.asset_type != 'organization' and not self.parent:
            raise ValidationError(f"A {self.asset_type} must have a parent asset.")

        if self.parent:
            if self.asset_type == 'organization':
                raise ValidationError("An Organization cannot have a parent asset.")
            if self.parent.asset_type == 'machine':
                raise ValidationError("A Machine cannot have a child asset.")

    def save(self, *args, **kwargs):
        self.full_clean()  # enforce validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_name} ({self.asset_type})"


class AssetDetail(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='details')

    location = models.CharField(max_length=255, blank=False, null=False)
    building = models.CharField(max_length=255, blank=False, null=False)
    floor = models.CharField(max_length=50, blank=True, null=True)
    room = models.CharField(max_length=255, blank=True, null=True)
    line = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Details of {self.asset.asset_name}"
