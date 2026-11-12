from rest_framework.permissions import BasePermission


class IsStaff(BasePermission):
    """Only signed-in staff accounts (created with `createsuperuser` or ticked "Staff" in /admin/)."""

    message = 'Admin access only.'

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_active and u.is_staff)
