from django import forms
from django.forms import ModelForm
from .models import Group
from django.core.exceptions import ValidationError

class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = {
            "user" : forms.HiddenInput()
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        special_char = ['!', '@', '#', '$', '%', '&', '*', "\\", "/", "."]
        for sc in special_char:
            if(sc in name):
                raise ValidationError("Group Name cannot contain special characters [!@#$%&*()\\/.]")

        return name