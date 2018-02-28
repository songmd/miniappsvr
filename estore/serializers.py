from rest_framework import serializers
from .models import *


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = ['pic']


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        exclude = []


class ShopInfoSerializer(serializers.ModelSerializer):
    banners = PictureSerializer(many=True)
    icon = PictureSerializer()
    notices = NoticeSerializer(many=True)
    serializers.StringRelatedField(many=True)

    class Meta:
        model = ShopInfo
        exclude = ['app_id', 'app_secret']


class ProductSerializer(serializers.ModelSerializer):
    pics = PictureSerializer(many=True)
    primary_pic = PictureSerializer()

    class Meta:
        model = Product
        fields = ['id', 'title', 'primary_pic', 'price', 'off_price', 'pics']


class BasketItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = BasketItem
        fields = ['product', 'quantity']


class DateTimeTzAwareField(serializers.DateTimeField):
    def to_representation(self, value):
        if not value:
            return None
        value = self.enforce_timezone(value)
        output_format = getattr(self, 'format')
        return value.strftime(output_format)


class OrderSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    order_no = serializers.SerializerMethodField(read_only=True)
    date_created = DateTimeTzAwareField(format="%Y年%m月%d日 %H:%M:%S", read_only=True)

    class Meta:
        model = Order
        exclude = []
        fields = ['order_no', 'status', 'date_created', 'amount', 'items']

    def get_order_no(self, obj):
        v1 = None
        return obj.id.hex


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        exclude = []
