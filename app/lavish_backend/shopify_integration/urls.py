from django.urls import path
from . import views

app_name = 'shopify_integration'

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('sync/', views.sync_data, name='sync_data'),
    path('webhook/', views.webhook_handler, name='webhook_handler'),
    path('stores/', views.store_list, name='store_list'),
    path('sync-operations/', views.sync_operations_list, name='sync_operations_list'),
]
