from django.urls import path
from . import views 
  
urlpatterns = [ 
    path('menu-items/', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.MenuItemDetailView.as_view()),
    path('groups/manager/users', views.GroupManagerView.as_view()),
    path('groups/manager/users/<int:pk>', views.GroupManagerDetailView.as_view()),
    path('groups/delivery-crew/users', views.GroupDeliveryView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.GroupDeliveryDetailView.as_view()),
    path('cart/menu-items/', views.CartItemView.as_view()),
    path('orders/', views.OrdersView.as_view()),
    path('orders/<int:pk>', views.OrderItemView.as_view()),
]
