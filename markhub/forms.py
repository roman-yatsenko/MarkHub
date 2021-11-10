from typing import Optional, Mapping, Union, Any, Type
from django import forms


class NewFileForm(forms.Form):
    """ New File Form"""

    filename = forms.CharField(max_length=256, label='File name', required=True)
    content = forms.CharField(widget=forms.Textarea, label='File content')


class UpdateFileForm(forms.Form):
    """ Update File Form"""

    filename = forms.CharField(max_length=256, label='File name', required=True, 
                               widget=forms.TextInput(attrs={'readonly':'readonly'}))
    content = forms.CharField(widget=forms.Textarea, label='File content')


class BranchSelector(forms.Form):
    """ Barnch Selector Form"""

    branch = forms.ChoiceField(required=True)
    
    # def __init__(self, data: Optional[Mapping[str, Any]] = ..., *args, **kwargs) -> None:
    #     super().__init__(data=data, *args, **kwargs)
    #     self.fields

