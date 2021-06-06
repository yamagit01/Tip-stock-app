from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

from .widgets import FileInputWithPreview

class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'icon')
        widgets = {
            'icon': FileInputWithPreview(),
        }


class SignupUserForm(SignupForm):
    pass
