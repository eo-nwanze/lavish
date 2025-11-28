from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('items/', views.inventory_item_list, name='inventory_item_list'),
    path('levels/', views.inventory_level_list, name='inventory_level_list'),
    path('locations/', views.location_list, name='location_list'),
]
