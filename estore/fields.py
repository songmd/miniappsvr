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
