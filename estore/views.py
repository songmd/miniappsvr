import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .weixin import WxApi
from estore.serializers import *
from rest_framework import generics
from django.db import transaction
from django.urls import reverse


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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

        # 有js_code 则user_token不生效
        if js_code is not None:
            wx_data = WxApi.get_openid(shop.app_id, shop.app_secret, js_code)
            if 'errcode' in wx_data:
                resp['retcode'] = RetCode.WXSRV_ERROR
                return HttpResponse(json.dumps(resp), content_type="application/json")
            try:
                customer = AppCustomer.objects.get(openid=wx_data['openid'], shop=shop)
                resp['user_token'] = customer.id.hex
            except AppCustomer.DoesNotExist:
                customer = AppCustomer.objects.create(shop=shop)
                customer.openid = wx_data['openid']
                customer.shop = shop
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
            customer = AppCustomer.objects.get(pk=user_token, shop=shop)
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


# b'<xml>
# <appid><![CDATA[wx773060da4bef94cc]]></appid>\n
# <bank_type><![CDATA[CFT]]></bank_type>\n
# <cash_fee><![CDATA[1]]></cash_fee>\n
# <fee_type><![CDATA[CNY]]></fee_type>\n
# <is_subscribe><![CDATA[N]]></is_subscribe>\n
# <mch_id><![CDATA[1498624892]]></mch_id>\n
# <nonce_str><![CDATA[IeSv6kZG4whqw62q5bUrYAZcPlTkt06F]]></nonce_str>\n
# <openid><![CDATA[oAu0e5V9v2dmoEKEtPXYdQQKg4kw]]></openid>\n
# <out_trade_no><![CDATA[718f68130f0d4f6da4b717e96e7ea453]]></out_trade_no>\n
# <result_code><![CDATA[SUCCESS]]></result_code>\n
# <return_code><![CDATA[SUCCESS]]></return_code>\n
# <sign><![CDATA[880A8EAC666F1C097DFB7222BF71C0BA]]></sign>\n
# <time_end><![CDATA[20180302095348]]></time_end>\n
# <total_fee>1</total_fee>\n
# <trade_type><![CDATA[JSAPI]]></trade_type>\n
# <transaction_id><![CDATA[4200000053201803021002785040]]></transaction_id>\n
# </xml>'
@csrf_exempt
def wxpay_notify(request):
    data = WxApi.to_dict(request.body)
    resp = {}
    if data['return_code'] != 'SUCCESS':
        print('pay notify failed,%s' % data['return_msg'])
        resp['return_code'] = 'SUCCESS'
        return HttpResponse(WxApi.to_xml(resp), content_type="application/xml")

    order = Order.objects.all().get(out_trade_no=data['out_trade_no'])
    merchant = order.customer.shop.merchant

    wxapi = WxApi('', '', merchant.mch_key, '')
    sign = data.pop('sign', None)
    real_sign = wxapi.sign(data, 'MD5')
    if sign != real_sign:
        resp['return_code'] = 'FAIL'
        resp['return_msg'] = 'wrong sign'
        print('pay notify failed,%s' % data['return_msg'])
        return HttpResponse(WxApi.to_xml(resp), content_type="application/xml")
    order.status = 1
    order.save()
    resp['return_code'] = 'SUCCESS'
    return HttpResponse(WxApi.to_xml(resp), content_type="application/xml")


def ask_for_pay(request):
    resp = {}
    order_no = request.GET.get('order_no', None)
    if order_no is None:
        resp['retcode'] = RetCode.INVALID_PARA
        return HttpResponse(json.dumps(resp), content_type="application/json")

    order = Order.objects.get(pk=uuid.UUID(order_no))
    wxapi = WxApi(order.customer.shop.app_id,
                  order.customer.shop.merchant.mch_id,
                  order.customer.shop.merchant.mch_key,
                  request.build_absolute_uri(reverse('wxpay_notify')),
                  key=order.customer.shop.merchant.key_file.path,
                  cert=order.customer.shop.merchant.cert_file.path
                  )
    wx_data = wxapi.jsapi_unified_order(body=order.summary(),
                                        out_trade_no=order.out_trade_no.hex,
                                        total_fee=int(order.amount() * 100),
                                        spbill_create_ip=get_client_ip(request),
                                        limit_pay='no_credit',
                                        openid=order.customer.openid)
    if wx_data is None:
        resp['retcode'] = RetCode.WXSRV_ERROR
    else:
        resp['retcode'] = RetCode.SUCCESS
        resp.update(wx_data)
        # resp['prepay'] = wx_data
        print(wx_data)

    # comment = wxapi.pull_comment('20180201000000', '20180211000000')
    # print(comment)
    return HttpResponse(json.dumps(resp), content_type="application/json")


class ShopInfoDetail(generics.RetrieveAPIView):
    queryset = ShopInfo.objects.all()
    serializer_class = ShopInfoSerializer


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop_id', None)
        if shop_id is None:
            return Product.objects.all().none()
        queryset = Product.objects.filter(shop=shop_id)
        return queryset


class ProductDetail(generics.RetrieveAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop_id', None)
        if shop_id is None:
            return Product.objects.all().none()
        queryset = Product.objects.filter(shop=shop_id)
        return queryset


# class BasketItemList(generics.ListCreateAPIView):
#     serializer_class = BasketItemSerializer
#
#     def get_queryset(self):
#         return BasketItem.objects.all().filter(belong_customer=self.kwargs['user_token'])
#
#
# class BasketItemDelete(generics.DestroyAPIView):
#     serializer_class = BasketItemSerializer
#
#     def get_queryset(self):
#         return BasketItem.objects.all().filter(belong_customer=self.kwargs['user_token'])


class OrderList(generics.ListCreateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(customer=self.kwargs['user_token'], status__gte=0).order_by(
            '-date_created')

    def create(self, request, *args, **kwargs):
        resp = {}
        if 'user_token' not in kwargs:
            resp['retcode'] = RetCode.INVALID_PARA
            return HttpResponse(json.dumps(resp), content_type="application/json")
        customer = AppCustomer.objects.get(pk=kwargs['user_token'])
        address = request.data['address']
        order = Order(customer=customer,
                      name=address['name'],
                      mobile=address['mobile'],
                      province=address['province'],
                      city=address['city'],
                      district=address['district'],
                      detail_addr=address['detail_addr'],
                      zip_code=address['zip_code'])
        if 'remark' in request.data:
            order.remark = request.data['remark']
        with transaction.atomic():
            order.save()
            for item in request.data['items']:
                basket_item = BasketItem(product_id=item['product'],
                                         quantity=item['quantity'],
                                         price=item['price'],
                                         belong_order=order)
                basket_item.save()
        resp['retcode'] = RetCode.SUCCESS
        resp['order_no'] = order.id.hex
        return HttpResponse(json.dumps(resp), content_type="application/json")
        # if 'product' in request.data:
        #     if 'quantity' not in request.data or 'price' not in request.data:
        #         resp['retcode'] = RetCode.INVALID_PARA
        #         return HttpResponse(json.dumps(resp), content_type="application/json")
        #     item = BasketItem(product_id=request.data['product'],
        #                       quantity=request.data['quantity'],
        #                       price=request.data['price'])
        #     order = Order(customer=customer)
        #     item.belong_order = order
        #     with transaction.atomic():
        #         order.save()
        #         item.save()
        #     resp['retcode'] = RetCode.SUCCESS
        #     resp['order_no'] = order.id.hex
        # elif 'item' in request.data:
        #     if len(request.data['item']) <= 0:
        #         resp['retcode'] = RetCode.INVALID_PARA
        #         return HttpResponse(json.dumps(resp), content_type="application/json")
        #     with transaction.atomic():
        #         order = Order(customer=customer)
        #         order.save()
        #         for iid in request.data['item']:
        #             item = BasketItem.objects.get(pk=iid)
        #             if item.belong_order is not None or item.belong_customer is None:
        #                 raise ()
        #             item.belong_customer = None
        #             item.belong_order = order
        #             item.save()
        #     resp['retcode'] = RetCode.SUCCESS
        #     resp['order_no'] = order.id.hex
        # return HttpResponse(json.dumps(resp), content_type="application/json")


class OrderDetail(generics.UpdateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(customer=self.kwargs['user_token'])


class CustomerAddressList(generics.ListCreateAPIView):
    serializer_class = CustomerAddressSerializer

    def get_queryset(self):
        return CustomerAddress.objects.all().filter(customer=self.kwargs['user_token'])


class CustomerAddressDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer

    def get_queryset(self):
        return CustomerAddress.objects.all().filter(customer=self.kwargs['user_token'])


class CustomerCommentCreate(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        resp = {}
        if ('order' not in request.data) or ('items' not in request.data):
            resp['retcode'] = RetCode.INVALID_PARA
            return HttpResponse(json.dumps(resp), content_type="application/json")
        order = Order.objects.get(pk=request.data['order'])
        order.status = 4
        with transaction.atomic():
            for item in request.data['items']:
                customer_comment = CustomerComment(product_id=item['product'],
                                                   order=order,
                                                   score=item['score'],
                                                   comment=item['comment'])
                customer_comment.save()
            order.save()

        resp['retcode'] = RetCode.SUCCESS

        return HttpResponse(json.dumps(resp), content_type="application/json")
