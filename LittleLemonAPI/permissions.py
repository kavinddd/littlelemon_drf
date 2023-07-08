from rest_framework import permissions

class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.is_authenticated
        return request.user.groups.filter(name='Manager').exists()
    

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Customer').exists()

