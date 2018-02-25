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
