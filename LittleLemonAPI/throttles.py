from rest_framework.throttling import UserRateThrottle

class ManagerThrottle(UserRateThrottle):
    rate = "50/minute"
    scope = 'manager'
    def allow_request(self, request, view):
        user = request.user
        if user.groups.filter(name="Manager").exists():
            print('TEST MANAGER')
            return super().allow_request(request, view)
        return True

class DeliveryThrottle(UserRateThrottle):
    rate = "40/minute"
    scope = 'delivery'
    def allow_request(self, request, view):
        user = request.user
        if user.groups.filter(name="DeliveryCrew").exists():
            return super().allow_request(request, view)
        return True

class CustomerThrottle(UserRateThrottle):
    rate = "40/minute"
    scope = 'customer'
    def allow_request(self, request, view):
        user = request.user
        if user.groups.filter(name="Customer").exists():
            return super().allow_request(request, view)
        return True
