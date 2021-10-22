from django import forms


class EditFileForm(forms.Form):
    """ Edit File Form (create, update)"""

    filename = forms.CharField(max_length=256, label='File name', required=True)
    content = forms.CharField(widget=forms.Textarea, label='File content')
