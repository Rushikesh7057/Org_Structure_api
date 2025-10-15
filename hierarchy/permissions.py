from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Modified permission: allows any authenticated user to access Assets,
    since Asset model has no owner field.
    """
    def has_object_permission(self, request, view, obj):
        # Allow safe methods for all
        if request.method in SAFE_METHODS:
            return True
        # Allow write methods for authenticated users
        return request.user and request.user.is_authenticated
