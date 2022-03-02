from typing import Optional, Mapping, Union, Any, Type
from django import forms

from martor.fields import MartorFormField


class NewFileForm(forms.Form):
    """ New File Form"""

    filename = forms.CharField(max_length=256, label='File name', required=True)
    content = MartorFormField(label='File content')


class UpdateFileForm(forms.Form):
    """ Update File Form"""

    filename = forms.CharField(max_length=256, label='File name', required=True, 
                               widget=forms.TextInput(attrs={'readonly':'readonly'}))
    content = MartorFormField(label='File content')


class BranchSelector(forms.Form):
    """ Branch Selector Form"""

    branch = forms.ChoiceField(required=True, widget=forms.Select(attrs={'onchange':"this.form.submit()"}))
    
    def __init__(self, current_branch: str = '', branches: list = [], 
                *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['branch'].widget.choices = [(branch, branch) for branch in branches]
        self.fields['branch'].initial = current_branch
