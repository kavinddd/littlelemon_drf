from rest_framework import serializers
from . import models
from django.contrib.auth.models import User, Group
import datetime
from djoser.serializers import UserCreateSerializer

class CustomerUserCreateSerializer(UserCreateSerializer):
    def create(self, validated_data):
        user = super().create(validated_data)
        customer_group = Group.objects.get(name='Customer')
        customer_group.user_set.add(user)
        return user

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MenuItem
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                              default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Cart
        fields = '__all__'
        
    def create(self, validated_data):
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        unit_price = menuitem.price
        price = unit_price * quantity

        validated_data['unit_price'] = unit_price
        validated_data['price'] = price

        return super().create(validated_data)
        
class OrderItemSerializer(serializers.ModelSerializer):
    menu_title = serializers.StringRelatedField(source='menuitem', read_only=True)
    class Meta:
        model = models.OrderItem
        fields = '__all__' 

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                         default=serializers.CurrentUserDefault())
    
    orderitem = OrderItemSerializer(read_only=True, many=True, source='orderitem_set')

    class Meta:
        model = models.Order
        fields = ['id', 'user', 'date', 'delivery_crew', 'status', 'total', 'orderitem']

    def create(self, validated_data):  
        validated_data['date'] = datetime.date.today() 
        validated_data['total'] = self.get_total()
        return super().create(validated_data)

    def get_total(self):
        user_id = self.context['request'].user.id
        queryset = models.Cart.objects.filter(user=user_id)
        return sum(item.price for item in queryset)