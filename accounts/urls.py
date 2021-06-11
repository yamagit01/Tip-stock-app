from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path("password/set/", views.PasswordSetView.as_view(), name="account_set_password"),
    path("password/change/", views.PasswordChangeView.as_view(), name="account_change_password"),
]
