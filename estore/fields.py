from django.db import models
from .widgets import *


class ManyToManyFieldWithDDW(models.ManyToManyField):
    def formfield(self, **kwargs):
        kwargs['widget'] = DropdownSelectMultiple(attrs={'class': 'dropdown-ms'})
        return super().formfield(**kwargs)


class ImageFieldEx(models.ImageField):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgWidget
        return super().formfield(**kwargs)


class ForeignImgField(models.ForeignKey):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgSelectWidget(attrs={'class': 'foreign-img-field'})
        return super().formfield(**kwargs)


class ManyToManyImgField(models.ManyToManyField):
    def formfield(self, **kwargs):
        kwargs['widget'] = ImgSelectMultipleWidget(attrs={'class': 'img-dropdown-ms many-to-many-img-field'})
        # kwargs['to_field_name'] = 'pic'
        return super().formfield(**kwargs)
