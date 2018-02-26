import json
from django.contrib import admin

from django.contrib.auth.models import User

from mptt.admin import MPTTModelAdmin

from .models import *

from .widgets import *

admin.AdminSite.site_header = '三语信息技术有限公司'
# admin.AdminSite.site_url = None
admin.AdminSite.index_title = '首页'


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_picture', 'creator', 'display_path',)
    list_display_links = ('title', 'display_picture', 'display_path',)

    def response_add(self, request, obj, post_url_continue=None):
        ts = super().response_add(request, obj, post_url_continue)
        if '_popup' in request.POST:
            objdict = dict(value=obj.id, obj='##@@%s##@@%s' % (str(obj), obj.pic.url))
            ts.context_data['popup_response_data'] = json.dumps(objdict)
        return ts

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creator=request.user)

    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'creator_id') and obj.creator_id is None:
            obj.creator_id = request.user.id
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return super().has_add_permission(request) or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return has_perm or for_staff_show or creator == request.user

    def has_delete_permission(self, request, obj=None):
        has_perm = super().has_delete_permission(request, obj)
        if has_perm:
            return True
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return for_staff_show or creator == request.user


class NoticeInline(admin.TabularInline):
    template = 'tabular.html'
    model = Notice

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    @property
    def media(self):
        return super().media + forms.Media(css={'all': ('css/estore.css',)})


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "icon":
                kwargs["queryset"] = Picture.objects.filter(creator=request.user)
            if db_field.name == "merchant":
                kwargs["queryset"] = AppMerchant.objects.filter(user_id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "banners":
                kwargs["queryset"] = Picture.objects.filter(creator=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(merchant=request.user.merchant)

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner = False
        if obj is not None and obj.merchant == getattr(request.user, 'merchant', None):
            is_owner = True
        return has_perm or for_staff_show or is_owner

    inlines = [NoticeInline]
    readonly_fields = ('display_id',)
    fields = (('display_id',), ('title', 'merchant'),
              ('app_id', 'app_secret'), ('address', 'phone_num'),
              ('longitude', 'latitude'), 'description', 'icon', 'banners')


@admin.register(AppMerchant)
class AppMerchantAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.user.is_staff:
            obj.user.is_staff = True
            obj.user.save()
            # obj.save()
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user" and not request.user.is_superuser:
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user_id=request.user.id)

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner_obj = getattr(obj, 'user', None) == request.user
        return has_perm or for_staff_show or is_owner_obj


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'price', 'off_price')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(shop__merchant=getattr(request.user, 'merchant', None))

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return super().has_add_permission(request) or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner = False
        if obj is not None and obj.shop.merchant == getattr(request.user, 'merchant', None):
            is_owner = True
        return has_perm or for_staff_show or is_owner

    def has_delete_permission(self, request, obj=None):
        has_perm = super().has_delete_permission(request, obj)
        if has_perm:
            return True
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return for_staff_show or creator == request.user

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "shop":
                kwargs["queryset"] = ShopInfo.objects.filter(merchant=getattr(request.user, 'merchant', None))
            if db_field.name == "primary_pic":
                kwargs["queryset"] = Picture.objects.filter(creator=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "categories":
                kwargs["queryset"] = ProductCategory.objects.filter(creator=request.user)
            if db_field.name == "pics":
                kwargs["queryset"] = Picture.objects.filter(creator=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(ProductCategory)
class ProductCategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'creator')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = ProductCategory.objects.filter(creator=request.user)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creator_id=request.user.id)

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'creator_id') and obj.creator_id is None:
            obj.creator_id = request.user.id
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return super().has_add_permission(request) or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return has_perm or for_staff_show or creator == request.user

    def has_delete_permission(self, request, obj=None):
        has_perm = super().has_delete_permission(request, obj)
        if has_perm:
            return True
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return for_staff_show or creator == request.user


@admin.register(AppCustomer)
class AppCustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'openid')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(shop__merchant=getattr(request.user, 'merchant', None))

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner = False
        if obj is not None and obj.shop.merchant == getattr(request.user, 'merchant', None):
            is_owner = True
        return has_perm or for_staff_show or is_owner


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'customer')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(customer__shop__merchant=getattr(request.user, 'merchant', None))

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner = False
        if obj is not None and obj.customer.shop.merchant == getattr(request.user, 'merchant', None):
            is_owner = True
        return has_perm or for_staff_show or is_owner


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ('display_product', 'price', 'quantity', 'date_created', 'belong_order')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(product__shop__merchant=getattr(request.user, 'merchant', None))

    def has_module_permission(self, request):
        if super().has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_owner = False
        if obj is not None and obj.product.shop.merchant == getattr(request.user, 'merchant', None):
            is_owner = True
        return has_perm or for_staff_show or is_owner
