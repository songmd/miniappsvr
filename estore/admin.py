import json
from django.contrib import admin
from django.forms import ModelForm

from mptt.admin import MPTTModelAdmin

from .models import *

from .widgets import *

admin.AdminSite.site_header = '三语信息技术有限公司'
# admin.AdminSite.site_url = None
admin.AdminSite.index_title = '首页'


class EstoreModelAdminMixin(object):

    def has_module_permission(self, request):
        if super(EstoreModelAdminMixin, self).has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff

    def get_queryset(self, request):
        qs = super(EstoreModelAdminMixin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creator=request.user)

    def save_model(self, request, obj, form, change):

        if hasattr(obj, 'creator_id') and obj.creator_id is None:
            obj.creator_id = request.user.id
        super(EstoreModelAdminMixin, self).save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return super(EstoreModelAdminMixin, self).has_add_permission(request) or request.user.is_staff

    def has_change_permission(self, request, obj=None):

        has_perm = super(EstoreModelAdminMixin, self).has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return has_perm or for_staff_show or creator == request.user

    def has_delete_permission(self, request, obj=None):
        has_perm = super(EstoreModelAdminMixin, self).has_delete_permission(request, obj)
        if has_perm:
            return True
        for_staff_show = request.user.is_staff and obj is None
        creator = getattr(obj, 'creator', None)
        return for_staff_show or creator == request.user


@admin.register(Picture)
class PictureAdmin(EstoreModelAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'display_picture', 'display_path',)
    list_display_links = ('title', 'display_picture', 'display_path',)

    def response_add(self, request, obj, post_url_continue=None):
        ts = super(PictureAdmin, self).response_add(request, obj, post_url_continue)
        IS_POPUP_VAR = '_popup'
        if IS_POPUP_VAR in request.POST:
            objdict = dict(value=obj.id, obj='##@@%s##@@%s' % (str(obj), obj.pic.url))
            ts.context_data['popup_response_data'] = json.dumps(objdict)
        return ts


class NoticeInline(EstoreModelAdminMixin, admin.TabularInline):
    template = 'tabular.html'
    model = Notice

    @property
    def media(self):
        return super(NoticeInline, self).media + forms.Media(css={'all': ('css/estore.css',)})


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):

        if hasattr(obj, 'creator_id') and obj.creator_id is None:
            obj.creator_id = request.user.id
        super(ShopInfoAdmin, self).save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "icon":
            kwargs["queryset"] = Picture.objects.filter(creator=request.user)
        return super(ShopInfoAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        if super(ShopInfoAdmin, self).has_module_permission(request):
            return True
        return request.user.is_superuser or request.user.is_staff


    def get_queryset(self, request):
        qs = super(ShopInfoAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creator=request.user)


    def has_change_permission(self, request, obj=None):
        has_perm = super(ShopInfoAdmin, self).has_change_permission(request, obj)
        for_staff_show = request.user.is_staff and obj is None
        is_creator_obj = getattr(obj, 'creator', None) == request.user
        return has_perm or for_staff_show or is_creator_obj

    inlines = [NoticeInline]
    readonly_fields = ('display_id',)
    fields = (('display_id',), ('title', 'merchant'),
              ('app_id', 'app_secret'), ('address', 'phone_num'),
              ('longitude', 'latitude'), 'description', 'icon', 'banners')


@admin.register(AppMerchant)
class AppMerchantAdmin(admin.ModelAdmin):
    pass


@admin.register(AppCustomer)
class AppCustomerAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(EstoreModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ProductCategory)
class ProductCategoryAdmin(EstoreModelAdminMixin, MPTTModelAdmin):
    list_display = ('name', 'parent')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = ProductCategory.objects.filter(creator=request.user)

        return super(ProductCategoryAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
