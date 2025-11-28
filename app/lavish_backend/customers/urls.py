from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('<str:shopify_id>/', views.customer_detail, name='customer_detail'),
    path('sync/', views.sync_customers, name='sync_customers'),
]
