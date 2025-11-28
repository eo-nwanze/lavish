from django.db import models

class Country(models.Model):
    """Model for storing countries with their codes and information"""
    name = models.CharField(max_length=100, unique=True)
    iso_code = models.CharField(max_length=2, unique=True)  # ISO 3166-1 alpha-2
    iso3_code = models.CharField(max_length=3, unique=True)  # ISO 3166-1 alpha-3
    phone_code = models.CharField(max_length=10)  # International phone code
    currency = models.CharField(max_length=3, blank=True)  # Currency code
    currency_symbol = models.CharField(max_length=5, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    flag_emoji = models.CharField(max_length=10, blank=True)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.flag_emoji} {self.name} (+{self.phone_code})"

class State(models.Model):
    """Model for storing states/provinces within countries"""
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    state_code = models.CharField(max_length=10, blank=True)  # State abbreviation
    
    class Meta:
        unique_together = ['name', 'country']
        ordering = ['country', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"

class City(models.Model):
    """Model for storing cities within states"""
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Cities"
        unique_together = ['name', 'state']
        ordering = ['state', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.state.name}, {self.state.country.name}"
