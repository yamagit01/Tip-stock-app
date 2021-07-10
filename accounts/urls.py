from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('your_profile/<int:pk>/', views.YourProfileView.as_view(), name='your_profile'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path("password/set/", views.PasswordSetView.as_view(), name="account_set_password"),
    path("password/change/", views.PasswordChangeView.as_view(), name="account_change_password"),
    path("withdrawal/", views.WithdrawalView.as_view(), name="withdrawal"),
    path("withdrawal_done/", views.WithdrawalDoneView.as_view(), name="withdrawal_done"),
    path("reregistration/", views.ReRegistrationView.as_view(), name="reregistration"),
    path('follow_user/<int:pk>/', views.follow_user, name='follow_user'),
    path('unfollow_user/<int:pk>/', views.unfollow_user, name='unfollow_user'),
    path('followers/<int:pk>/', views.follows, name='followers'),
    path('follows/<int:pk>/', views.follows, name='follows'),
]
