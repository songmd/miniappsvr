import json
from django.http import HttpResponse
from .weixin import WxApi
from estore.serializers import *
from rest_framework import generics
from django.db import transaction


class RetCode(object):
    SUCCESS = '0000'
    INVALID_PARA = '0001'
    USER_NOT_EXIST = '0002'
    SHOP_NOT_EXIST = '0003'
    WXSRV_ERROR = '0004'
    SRV_EXCEPTION = '0005'


def customer_login(request):
    resp = {}
    js_code = request.GET.get('js_code', None)
    user_token = request.GET.get('user_token', None)
    shop_id = request.GET.get('shop_id', None)
    user_info = request.GET.get('user_info', None)

    try:
        if shop_id is None:
            resp['retcode'] = RetCode.INVALID_PARA
            return HttpResponse(json.dumps(resp), content_type="application/json")

        shop = ShopInfo.objects.get(pk=uuid.UUID(shop_id))
        if shop is None:
            resp['retcode'] = RetCode.SHOP_NOT_EXIST
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # 有js_code 则user_token不生效
        if js_code is not None:
            wx_data = WxApi.get_openid(shop.app_id, shop.app_secret, js_code)
            if 'errcode' in wx_data:
                resp['retcode'] = RetCode.WXSRV_ERROR
                return HttpResponse(json.dumps(resp), content_type="application/json")
            try:
                customer = AppCustomer.objects.get(openid=wx_data['openid'], belong=shop)
                resp['user_token'] = customer.id.hex
            except AppCustomer.DoesNotExist:
                customer = AppCustomer.objects.create(belong=shop)
                customer.openid = wx_data['openid']
                customer.belong = shop
                resp['user_token'] = customer.id.hex

            customer.session_key = wx_data['session_key']
            if 'unionid' in wx_data:
                customer.unionid = wx_data['unionid']
            if user_info:
                customer.user_info = user_info
            customer.save()

            # login(request, customer)
            resp['retcode'] = RetCode.SUCCESS
            return HttpResponse(json.dumps(resp), content_type="application/json")

        if user_token is not None:
            customer = AppCustomer.objects.get(pk=user_token, belong=shop)
            if customer is None:
                resp['retcode'] = RetCode.USER_NOT_EXIST
                return HttpResponse(json.dumps(resp), content_type="application/json")
            # login(request, customer)
            resp['retcode'] = RetCode.SUCCESS

            if user_info != customer.user_info:
                customer.user_info = user_info
                customer.save()

            return HttpResponse(json.dumps(resp), content_type="application/json")
    except BaseException as e:
        print(e)
        resp['retcode'] = RetCode.SRV_EXCEPTION
        return HttpResponse(json.dumps(resp), content_type="application/json")

    resp['retcode'] = RetCode.INVALID_PARA
    return HttpResponse(json.dumps(resp), content_type="application/json")


def ask_for_pay(request):
    pass


class ShopInfoDetail(generics.RetrieveAPIView):
    queryset = ShopInfo.objects.all()
    serializer_class = ShopInfoSerializer


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop_id', None)
        if shop_id is None:
            return Product.objects.all().none()
        queryset = Product.objects.filter(belong=shop_id)
        return queryset


class BasketItemList(generics.ListCreateAPIView):
    serializer_class = BasketItemSerializer

    def get_queryset(self):
        return BasketItem.objects.all().filter(belong_customer=self.kwargs['user_token'])


class BasketItemDelete(generics.DestroyAPIView):
    serializer_class = BasketItemSerializer

    def get_queryset(self):
        return BasketItem.objects.all().filter(belong_customer=self.kwargs['user_token'])


class OrderList(generics.ListCreateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(belong=self.kwargs['user_token'])

    def create(self, request, *args, **kwargs):
        resp = {}
        if 'user_token' not in kwargs:
            resp['retcode'] = RetCode.INVALID_PARA
            return HttpResponse(json.dumps(resp), content_type="application/json")
        customer = AppCustomer.objects.get(pk=kwargs['user_token'])
        if 'product' in request.data:
            if 'quantity' not in request.data or 'price' not in request.data:
                resp['retcode'] = RetCode.INVALID_PARA
                return HttpResponse(json.dumps(resp), content_type="application/json")
            item = BasketItem(product_id=request.data['product'],
                              quantity=request.data['quantity'],
                              price=request.data['price'])
            order = Order(belong=customer)
            item.belong_order = order
            with transaction.atomic():
                order.save()
                item.save()
            resp['retcode'] = RetCode.SUCCESS
            resp['order_no'] = order.id.hex
        elif 'item' in request.data:
            if len(request.data['item']) <= 0:
                resp['retcode'] = RetCode.INVALID_PARA
                return HttpResponse(json.dumps(resp), content_type="application/json")
            with transaction.atomic():
                order = Order(belong=customer)
                order.save()
                for iid in request.data['item']:
                    item = BasketItem.objects.get(pk=iid)
                    if item.belong_order is not None or item.belong_customer is None:
                        raise()
                    item.belong_customer = None
                    item.belong_order = order
                    item.save()
            resp['retcode'] = RetCode.SUCCESS
            resp['order_no'] = order.id.hex
        return HttpResponse(json.dumps(resp), content_type="application/json")


class OrderDetail(generics.RetrieveAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(belong=self.kwargs['user_token'])
