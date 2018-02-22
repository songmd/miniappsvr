import uuid
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class AppMerchant(models.Model):
    user = models.OneToOneField('auth.User', related_name='merchant', on_delete=models.CASCADE, verbose_name=_('关联用户'))
    mch_id = models.CharField(_('商户微信支付Id'), max_length=128, blank=True, null=True)
    mch_key = models.CharField(_('商户微信支付密钥'), max_length=128, blank=True, null=True)
    key_file = models.FileField(_('密钥文件'), blank=True, null=True, upload_to='cert')
    cert_file = models.FileField(_('证书文件'), blank=True, null=True, upload_to='cert')

    class Meta:
        verbose_name = _('商户')
        verbose_name_plural = _('商户')

    def __str__(self):
        return self.user.username


class AppCustomer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    belong = models.ForeignKey('ShopInfo', on_delete=models.CASCADE, verbose_name=_('所属店铺'))
    openid = models.CharField(_('微信OpenId'), max_length=128)
    session_key = models.CharField(_('会话密钥'), max_length=128)
    unionid = models.CharField(_('统一Id'), max_length=128, null=True)
    user_info = models.TextField(_('用户信息'), max_length=512, null=True)

    # basket = models.ManyToManyField('BasketItem', related_name='customer', verbose_name=_('购物栏'))

    def display_id(self):
        return self.id.hex

    display_id.short_description = _('ID')

    class Meta:
        verbose_name = _('客户')
        verbose_name_plural = _('客户')

    def __str__(self):
        return self.id.hex


# 购物蓝中或者订单中的某一项
class BasketItem(models.Model):
    # 要么属于订单，要么属于购物篮
    belong_customer = models.ForeignKey('AppCustomer', on_delete=models.CASCADE, null=True, verbose_name=_("所属客户"))
    belong_order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, verbose_name=_("所属订单"))

    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name=_("商品"))
    quantity = models.PositiveIntegerField(_('数量'), default=1)
    price = models.DecimalField(_('成交价格'), decimal_places=2, max_digits=12)
    date_created = models.DateTimeField(_("生成时间"), auto_now_add=True)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    belong = models.ForeignKey('AppCustomer', on_delete=models.CASCADE,
                               verbose_name=_('所属客户'))

    STATUS_CHOICES = (
        ('unpay', _("未支付")),
        ('payed', _("已支付")),
        ('undeliver', _("等待发货")),
        ('deliving', _("正在运送")),
        ('delived', _("已送达")),
        ('confirm', _("已确认")),
    )

    status = models.CharField(_("订单状态"), max_length=32, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])

    class Meta:
        verbose_name = _("订单")
        verbose_name_plural = _("订单")


class EstoreModel(models.Model):
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, editable=False, verbose_name=_('创建者'))

    class Meta:
        abstract = True


class ShopInfo(EstoreModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    title = models.CharField(_('店铺名称'), max_length=32)

    app_id = models.CharField(_('小程序id'), max_length=128, blank=True, null=True)

    app_secret = models.CharField(_('小程序密钥'), max_length=128, blank=True, null=True)

    address = models.CharField(_('地址'), max_length=128, blank=True, null=True)

    phone_num = models.CharField(_('联系电话'), max_length=11, blank=True, null=True)

    longitude = models.FloatField(_('经度'), blank=True, null=True)

    latitude = models.FloatField(_('纬度'), blank=True, null=True)

    description = models.TextField(_('店铺描述'), max_length=512, blank=True, null=True, help_text=_('最多500个字符，250个汉字'))

    icon = models.ForeignKey('Picture', blank=True, null=True, verbose_name=_('店铺图标'), on_delete=models.SET_NULL)

    banners = models.ManyToManyField('Picture', blank=True, related_name='banners', verbose_name=_('广告图片'))

    def display_id(self):
        return self.id.hex

    display_id.short_description = _('ID')

    class Meta:
        verbose_name = _('店铺')
        verbose_name_plural = _('店铺')

    def __str__(self):
        return self.title


class Notice(EstoreModel):
    belong = models.ForeignKey('ShopInfo', related_name='notices', on_delete=models.CASCADE, verbose_name=_('所属店铺'))
    content = models.TextField(_('内容'), max_length=512, help_text=_('最多500个字符，250个汉字'))

    class Meta:
        verbose_name = _('公告')
        verbose_name_plural = _('公告')

    def __str__(self):
        return self.content


class Product(EstoreModel):
    belong = models.ForeignKey('ShopInfo', related_name='products', on_delete=models.CASCADE, blank=True, null=True,
                               verbose_name=_('所属商铺'))

    title = models.CharField(_('名称'), max_length=32)

    categories = models.ManyToManyField('ProductCategory', blank=True, verbose_name=_('所属分类'))

    primary_pic = models.OneToOneField('Picture', blank=True, null=True, verbose_name=_('首要图片'),
                                       on_delete=models.SET_NULL)

    price = models.FloatField(_('价格'))

    off_price = models.FloatField(_('折扣价格'), blank=True, null=True)

    pics = models.ManyToManyField('Picture', blank=True, related_name='pics', verbose_name=_('图片'))

    class Meta:
        verbose_name = _('商品')
        verbose_name_plural = _('商品')

    def __str__(self):
        return self.title


class Picture(EstoreModel):
    title = models.CharField(_('标题'), max_length=32)
    pic = models.ImageField(_('图片'), upload_to='estorepics')

    def display_picture(self):
        return format_html('<image src="{}" height="80px"></image>',
                           self.pic.url)

    display_picture.allow_tags = True
    display_picture.short_description = _('预览')

    def display_path(self):
        return self.pic.url

    display_path.short_description = _('路径')

    class Meta:
        verbose_name = _('图片')
        verbose_name_plural = _('图片')

    def __str__(self):
        return self.title


class ProductCategory(MPTTModel, EstoreModel):
    name = models.CharField(_('分类名称'), max_length=32)
    parent = TreeForeignKey('self', related_name='children', on_delete=models.SET_NULL, blank=True,
                            null=True,
                            verbose_name=_('上级分类'))

    def __str__(self):
        display = self.name
        pp = self.parent
        while pp is not None:
            display = '%s->%s' % (pp.name, display)
            pp = pp.parent
        return display

    class Meta:
        verbose_name = _('商品分类')
        verbose_name_plural = _('商品分类')
