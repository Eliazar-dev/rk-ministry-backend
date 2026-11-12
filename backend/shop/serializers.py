from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.CharField(source='image_src')

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'image', 'description')
