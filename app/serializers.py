from rest_framework import serializers

from app.models import SoldProduct, Products


class SoldProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoldProduct
        fields = ("listing_id", "image_url", "title", "store_name", "buy_price")


class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ("photo_id", "image_url", "title", "store_name", "buy_price")
