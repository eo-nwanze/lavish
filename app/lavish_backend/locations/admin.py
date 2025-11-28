from django.contrib import admin
from .models import Country, State, City

class StateInline(admin.TabularInline):
    model = State
    extra = 1
    show_change_link = True

class CityInline(admin.TabularInline):
    model = City
    extra = 1
    show_change_link = True

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'iso_code', 'phone_code', 'currency', 'flag_emoji']
    list_filter = ['currency']
    search_fields = ['name', 'iso_code', 'iso3_code']
    inlines = [StateInline]

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'state_code', 'country']
    list_filter = ['country']
    search_fields = ['name', 'state_code', 'country__name']
    inlines = [CityInline]

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'country_name']
    list_filter = ['state__country', 'state']
    search_fields = ['name', 'state__name', 'state__country__name']
    
    def country_name(self, obj):
        return obj.state.country.name
    country_name.short_description = 'Country'
