from rest_framework import serializers
from .models import *


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        exclude = ['creator']


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        exclude = ['creator']


class ShopInfoSerializer(serializers.ModelSerializer):
    banners = PictureSerializer(many=True)
    icon = PictureSerializer()
    notices = NoticeSerializer(many=True)
    serializers.StringRelatedField(many=True)

    class Meta:
        model = ShopInfo
        exclude = ['app_id', 'app_secret', 'creator']


class ProductSerializer(serializers.ModelSerializer):
    pics = PictureSerializer(many=True)
    primary_pic = PictureSerializer()

    class Meta:
        model = Product
        exclude = ['creator']


class BasketItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItem
        exclude = []
        # fields = ['product','price','quantity','date_created','customer']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = []
