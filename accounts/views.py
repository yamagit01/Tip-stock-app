from allauth.account import views
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from accounts.forms import ProfileForm
from accounts.models import User


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        return render(request, 'accounts/profile.html', {
            'user_data': user_data
        })
        

class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        form = ProfileForm(
            request.POST or None,
            initial = {
                'username': user_data.username,
                'icon': user_data.icon
            }
        )
        
        return render(request, 'accounts/profile_edit.html', {
            'form': form,
        })
        
    def post(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        form = ProfileForm(request.POST or None, instance=user_data)

        if form.is_valid():
            user_data.username = form.cleaned_data.get('username')
            if request.FILES:
                user_data.icon = request.FILES.get('icon')
            user_data.save()
            return redirect('accounts:profile')

        return render(request, 'accounts/profile_edit.html', {
            'form': form,
        })


class LoginView(views.LoginView):
    template_name = 'accounts/login.html'


@login_required
def logout_view(request):
    logout(request)
    return redirect('app:index')
    

class SignupView(views.SignupView):
    template_name = 'accounts/signup.html'


class PasswordChangeView(LoginRequiredMixin, views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')


class PasswordSetView(LoginRequiredMixin, views.PasswordSetView):
    success_url = reverse_lazy('accounts:profile')
