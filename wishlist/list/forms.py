from django import forms
from django.forms import ModelForm
from .models import Group

class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = {
            "user" : forms.HiddenInput()
        }