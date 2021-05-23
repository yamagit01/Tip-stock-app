from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('icon',)


class SignupUserForm(SignupForm):
    pass
