from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('sync/', views.order_sync, name='order_sync'),
    path('statistics/', views.order_statistics, name='order_statistics'),
    path('customer-orders/', views.customer_orders, name='customer_orders'),
    path('<str:shopify_id>/', views.order_detail, name='order_detail'),
    path('<str:shopify_id>/update-status/', views.order_update_status, name='order_update_status'),
    path('<str:shopify_id>/cancel/', views.order_cancel, name='order_cancel'),
    path('<str:shopify_id>/invoice/', views.order_invoice, name='order_invoice'),
    path('<str:shopify_id>/update-address/', views.order_update_address, name='order_update_address'),
    path('<str:shopify_id>/status/', views.order_status, name='order_status'),
]
