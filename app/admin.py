from django.contrib import admin
from .models import *

# Register your models here.
class Productsadmin(admin.ModelAdmin):
    search_fields = ['listing_id', 'title']  # add search fields
    list_display = [field.name for field in Products._meta.fields]


admin.site.register(Store)
admin.site.register(Products,Productsadmin)
admin.site.register(SoldProduct)
