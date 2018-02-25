from django.db import models
from .widgets import *


class ManyToManyFieldWithDDW(models.ManyToManyField):
    def formfield(self, **kwargs):
        kwargs['widget'] = DropdownSelectMultiple(attrs={'class': 'dropdown-ms'})
        return super(ManyToManyFieldWithDDW, self).formfield(**kwargs)


class ImageFieldEx(models.ImageField):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgWidget
        return super(ImageFieldEx, self).formfield(**kwargs)


# class OneToOneImgField(models.OneToOneField):
#     def formfield(self, **kwargs):
#         kwargs['widget'] = ImgSelectWidget
#         return super(OneToOneImgField, self).formfield(**kwargs)


class ForeignImgField(models.ForeignKey):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgSelectWidget(attrs={'class': 'foreign-img-field'})
        # kwargs['to_field_name'] = 'pic'
        return super(ForeignImgField, self).formfield(**kwargs)


class ManyToManyImgField(models.ManyToManyField):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgSelectMultipleWidget(attrs={'class': 'dropdown-ms many-to-many-img-field'})
        # kwargs['to_field_name'] = 'pic'
        return super(ManyToManyImgField, self).formfield(**kwargs)
