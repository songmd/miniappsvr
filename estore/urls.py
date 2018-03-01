from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'^login/$', views.customer_login, name='customer_login'),
    url(r'^askforpay/$', views.ask_for_pay, name='ask_for_pay'),
    url(r'^wxpaynotify/$', views.wxpay_notify, name='wxpay_notify'),
]
urlpatterns2 = [
    url(r'^shops/(?P<pk>[\w]+)/$', views.ShopInfoDetail.as_view()),

    url(r'^products/$', views.ProductList.as_view()),
    url(r'^products/(?P<pk>[\w]+)/$', views.ProductDetail.as_view()),
    # url(r'^basketitem/(?P<user_token>[\w]+)/$', views.BasketItemList.as_view()),
    # url(r'^basketitem/(?P<user_token>[\w]+)/(?P<pk>[\w]+)/$', views.BasketItemDelete.as_view()),
    url(r'^order/(?P<user_token>[\w]+)/$', views.OrderList.as_view()),
    url(r'^order/(?P<user_token>[\w]+)/(?P<pk>[\w]+)/$', views.OrderDetail.as_view()),

    url(r'^address/(?P<user_token>[\w]+)/$', views.CustomerAddressList.as_view()),
    url(r'^address/(?P<user_token>[\w]+)/(?P<pk>[\w]+)/$', views.CustomerAddressDetail.as_view()),

    url(r'^comment/$', views.CustomerCommentCreate.as_view()),

]
urlpatterns += format_suffix_patterns(urlpatterns2)
