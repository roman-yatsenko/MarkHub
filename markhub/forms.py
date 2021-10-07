from django import forms


class NewFileForm(forms.Form):
    """ New File Form """

    filename = forms.CharField(max_length=256, label='File name')
    content = forms.CharField(widget='Textarea', label='File content')
