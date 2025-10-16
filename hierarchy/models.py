from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Asset(models.Model):
    ASSET_TYPES = [
        ('organization', 'Organization'),
        ('group', 'Group'),
        ('subgroup', 'Subgroup'),
        ('plant', 'Plant'),
        ('location', 'Location'),
        ('Building', 'Building'),
        ('Floor', 'Floor'),
        ('Rooms', 'Rooms'),
        ('Line', 'Line'),
        ('other', 'Other'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES, db_index=True)
    hierarchy_level = models.PositiveIntegerField(default=0, editable=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', db_index=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default="2025-10-15")
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


