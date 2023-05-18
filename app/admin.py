from .models import *
from .utils import export_as_csv
from django.contrib import admin

admin.site.register(Store)
admin.site.register(SoldProduct)

class YourModelAdmin(admin.ModelAdmin):
    search_fields = ['listing_id', 'title']  # add search fields
    list_display = [field.name for field in Products._meta.fields]
    actions = [export_as_csv]

admin.site.register(Products, YourModelAdmin)
