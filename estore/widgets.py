from django import forms


class DropdownSelectMultiple(forms.Select):
    template_name = 'dropdownselectmultiple.html'
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get
        return getter(name)

    def value_omitted_from_data(self, data, files, name):
        # An unselected <select multiple> doesn't appear in POST data, so it's
        # never known if the value is actually omitted.
        return False

    class Media:
        js = ('js/jquery.min.js', 'js/multiple-select.js')
        css = {
            'all': ('css/multiple-select.css',)
        }


class ImgWidget(forms.ClearableFileInput):
    template_name = 'imgwidget.html'

    class Media:
        css = {
            'all': ('css/dropify.css',)
        }
        js = ('js/jquery.min.js', 'js/dropify.js',)


class ImgSelectWidget(forms.Select):
    template_name = 'imgselect.html'
    option_template_name = 'imgselectoption.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        from .models import Picture
        qs = Picture.objects.all()

        context['widget']['optgroups'][0][1][0]['attrs']['url'] = '/medias/img_not_select.png'

        for opt in context['widget']['optgroups'][1::]:
            opt[1][0]['attrs']['url'] = qs.get(pk=opt[1][0]['value']).pic.url
        return context

    class Media:
        js = ('js/jquery.min.js',)


class ImgSelectMultipleWidget(forms.Select):
    template_name = 'imgselectmultiple.html'
    option_template_name = 'imgselectoption.html'

    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get
        return getter(name)

    def value_omitted_from_data(self, data, files, name):
        # An unselected <select multiple> doesn't appear in POST data, so it's
        # never known if the value is actually omitted.
        return False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        from .models import Picture
        qs = Picture.objects.all()

        for opt in context['widget']['optgroups']:
            opt[1][0]['attrs']['url'] = qs.get(pk=opt[1][0]['value']).pic.url
        return context

    class Media:
        js = ('js/jquery.min.js', 'js/multiple-select.js')
        css = {
            'all': ('css/multiple-select.css',)
        }
