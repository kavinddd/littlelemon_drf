from . import permissions, models, serializers
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404 
from rest_framework.permissions import IsAuthenticated
import requests
from rest_framework.exceptions import PermissionDenied
from .pagination import StandardPagination

class MenuItemView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsManagerOrReadOnly]
    queryset = models.MenuItem.objects.all().order_by('id')
    serializer_class = serializers.MenuItemSerializer
    filterset_fields = ['id', 'category']
    pagination_class = StandardPagination
class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsManagerOrReadOnly]
    queryset = models.MenuItem.objects.all().order_by('id')

    serializer_class = serializers.MenuItemSerializer

class GroupManagerView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsManager]
    queryset = User.objects.filter(groups__name="Manager").order_by('id')

    serializer_class = serializers.UserSerializer

class GroupManagerDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsManager]
    queryset = User.objects.filter(groups__name="Manager").order_by('id')

    serializer_class = serializers.UserSerializer

class GroupDeliveryView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsManager]
    queryset = User.objects.filter(groups__name="DeliveryCrew").order_by('id')

    serializer_class = serializers.UserSerializer
    
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if username:
            username_object = get_object_or_404(User, username=username)
            delivery_crew_group = Group.objects.get(name="DeliveryCrew")
            delivery_crew_group.user_set.add(username_object)
            return Response({'message':'The user was assigned to a delivery crew group'}, status=201)
        return Response({'Error': 'username was not found'}, status=404)
    

class GroupDeliveryDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsManager]

    def delete(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        delivery_crew_list = User.objects.filter(groups__name="DeliveryCrew")
        username_object = get_object_or_404(delivery_crew_list, pk=id)
        if username_object:
            delivery_crew_group = Group.objects.get(name='DeliveryCrew')
            delivery_crew_group.user_set.remove(username_object)
            return Response({'message':'The user was removed from a delivery crew group'}, status=200)
        return Response({'error': 'userid was not found'}, status=404)

class CartItemView(APIView):
    permission_classes = [permissions.IsCustomer]
    def get(self, request):
        token = request.auth
        queryset = models.Cart.objects.filter(user__auth_token = token)
        serialized_item = serializers.CartItemSerializer(queryset, many=True)
        return Response(serialized_item.data, status=200)


    def post(self, request):
        cart_items = request.data
        serialized_item = serializers.CartItemSerializer(data=cart_items, context={'request':request})
        if serialized_item.is_valid():
            serialized_item.save()
            return Response(serialized_item.data, status=201)
        return Response(serialized_item.errors, status=400)

    def delete(self, request):
        cart_items = models.Cart.objects.filter(user_id = request.user.id)

        if cart_items.exists():
            cart_items.delete()
            return Response({'detail':'All the items have been removed'}, status=204)
        else:
            return Response({'errors': 'No cart items found for the user.'})

class OrdersView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    filterset_fields = ['status']
    def get_queryset(self):
        user_obj = self.request.user
        if user_obj.groups.filter(name='Customer').exists():
            queryset = models.Order.objects.filter(user = user_obj.id)
        elif user_obj.groups.filter(name='DeliveryCrew').exists():
            queryset = models.Order.objects.filter(delivery_crew = user_obj.id)
        elif user_obj.groups.filter(name='Manager').exists():
            queryset = models.Order.objects.all()
        else:
            return Response({'errors': 'Please try again'}, status=401)
        # Apply BackendFilter
        return queryset.order_by('id')

    def create(self, request, *args, **kwargs):
        user_obj = self.request.user
        if not (user_obj.groups.filter(name='Customer').exists()):
            return Response({'errors': 'You have no permission to perform this action'}, status=403)

        # get the current domain
        current_site = get_current_site(request)
        baseurl = f"{request.scheme}://{current_site.domain}" 

        # used to make a request to get and delete items in cart from other endpoints
        headers = {'Authorization': f'Token {self.request.auth}'}

        # Get items for current customer by using Cart endpoint
        response = requests.get(baseurl+'/api/cart/menu-items', headers=headers)
        cart_items = response.json()
        if len(cart_items) == 0 :
            return Response({'errors': 'The cart is empty'}, status=400)

        # Save to Order model (1 row)
        serializer_class = self.get_serializer_class()
        serialized_order = serializer_class(data={}, context={'request':request})

        # Save to OrderItem (many rows)
        serialized_order.is_valid(raise_exception=True)
        order = serialized_order.save()
        # Retrieve the order id (this possible after saving the data)
        order_id = order.id
        #  Create a data for order
        order_item_data = [{'order': order_id,
                            'menuitem': item['menuitem'],
                            'quantity': item['quantity'],
                            'unit_price': item['unit_price'],
                            'price': item['price']} for item in cart_items]
        serialized_order_item = serializers.OrderItemSerializer(data=order_item_data, many=True)

        serialized_order_item.is_valid(raise_exception=True)
        
        # Save to both tables then delete the cart
        serialized_order_item.save()
        requests.delete(baseurl+'/api/cart/menu-items', headers=headers)
        return Response(serialized_order_item.data, status=201)

class OrderItemView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    def get_queryset(self):
        user_obj = self.request.user
        queryset = models.Order.objects.all()
        if user_obj.groups.filter(name='Customer').exists():
            queryset = models.Order.objects.filter(user__id = user_obj.id)
        if user_obj.groups.filter(name='DeliveryCrew').exists():
            queryset =  models.Order.objects.filter(delivery_crew = user_obj.id)
        return queryset
    
    def perform_destroy(self, instance):
        user_obj = self.request.user
        if not user_obj.groups.filter(name='Manager').exists():
            raise PermissionDenied('You have to permission to perform this action')
        return super().perform_destroy(instance)

    def perform_update(self, serializer):
        method = self.request.method
        user_obj =  self.request.user
        if method == 'PUT':
           if not user_obj.groups.filter(name="Manager").exists():
                raise PermissionDenied('You have to permission to perform this action')
        elif method == 'PATCH':
            if user_obj.groups.filter(name="Customer").exists():
                raise PermissionDenied('You have to permission to perform this action')
        return super().perform_update(serializer)