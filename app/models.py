from django.db import models
from django.db.models import Q
from model_utils import Choices
from datetime import datetime, timedelta
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from django.core import serializers
import logging


# Create your models here.
class Store(models.Model):
    store_id = models.CharField(max_length=150, null=True, blank=True)
    store_name = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(auto_now=True, null=True, blank=True)
    action = models.CharField(max_length=10, default="active", null=True, blank=True)

    def __str__(self):
        return self.store_name


class Products(models.Model):
    listing_id = models.CharField(max_length=150, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    buy_price = models.CharField(max_length=10, null=True, blank=True)
    category_path = models.TextField(null=True, blank=True)
    photo_id = models.CharField(max_length=15, null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    sku_id = models.CharField(max_length=256, null=True, blank=True)
    available_to_buy = models.CharField(max_length=10, default=0, null=True, blank=True)
    quantity_remaining = models.CharField(
        max_length=10, default=0, null=True, blank=True
    )
    store_name = models.CharField(max_length=255, null=True, blank=True)
    sold_quantity = models.IntegerField(default=0, null=True, blank=True)
    date = models.CharField(max_length=10, null=True, blank=True)
    data_created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    data_updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    # start_date = models.DateField(null=True, blank=True)
    # end_date = models.DateField(null=True, blank=True)
    current_month = models.IntegerField(default=0, blank=True, null=True)
    last_month = models.IntegerField(default=0, blank=True, null=True)
    second_last_month = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.title

    def formatted_data_created_at(self):
        return self.data_created_at.strftime("%Y-%m-%d %I:%M:%S %p")

    def formatted_data_updated_at(self):
        return self.data_updated_at.strftime("%Y-%m-%d %I:%M:%S %p")


class SoldProduct(models.Model):
    listing_id = models.CharField(max_length=10, null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    buy_price = models.CharField(max_length=10, null=True, blank=True)
    sold_quantity = models.IntegerField(default=0, null=True, blank=True)
    date = models.CharField(max_length=10, null=True, blank=True)
    store_name = models.CharField(max_length=255, null=True, blank=True)
    