from rest_framework.permissions import BasePermission, SAFE_METHODS


class SolicitudAPIPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(view, 'action', None) == 'resolver':
            return user.has_perm('inventario.change_solicitud')
        if request.method in SAFE_METHODS:
            return user.has_perm('inventario.view_solicitud')
        if request.method == 'POST':
            return (
                user.has_perm('inventario.add_solicitud')
                and user.groups.filter(name='Auxiliares').exists()
            )
        if request.method in ('PUT', 'PATCH'):
            return user.has_perm('inventario.change_solicitud')
        if request.method == 'DELETE':
            return user.has_perm('inventario.delete_solicitud')
        return False
