from accounts import views as accounts_views
from allauth.account import views
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

urlpatterns = [
    # configのurlsでaccountsアプリのurlsはallauthより上に記載されているため、
    # accountsアプリのsignup等の処理でallauthのpathが適用されることはないが、
    # allauth内でname指定でpathを指定しているケースを考慮し、
    # allauthのpathもaccountsのviewが実行されるよう変更。
    
    # path("signup/", views.signup, name="account_signup"),
    # path("login/", views.login, name="account_login"),
    # path("logout/", views.logout, name="account_logout"),
    # path(
    #     "password/change/",
    #     views.password_change,
    #     name="account_change_password",
    # ),
    # path("password/set/", views.password_set, name="account_set_password"),
    
    path("signup/", accounts_views.SignupView.as_view(), name="account_signup"),
    path("login/", accounts_views.LoginView.as_view(), name="account_login"),
    path("logout/", accounts_views.logout_view, name="account_logout"),
    path(
        "password/change/",
        accounts_views.PasswordChangeView.as_view(),
        name="account_change_password",
    ),
    path("password/set/", accounts_views.PasswordSetView.as_view(), name="account_set_password"),
    
    path("inactive/", views.account_inactive, name="account_inactive"),
    # E-mail
    
    # emailの変更処理は現状使用不可の設定。homeにredirect。
    # path("email/", views.email, name="account_email"),
    path("email/", RedirectView.as_view(url="/"), name="account_email"),
    
    path(
        "confirm-email/",
        views.email_verification_sent,
        name="account_email_verification_sent",
    ),
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        views.confirm_email,
        name="account_confirm_email",
    ),
    # password reset
    path("password/reset/", views.password_reset, name="account_reset_password"),
    path(
        "password/reset/done/",
        views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
]

# ソーシャルアカウント関連
from importlib import import_module

from allauth import app_settings
from allauth.socialaccount import providers

if app_settings.SOCIALACCOUNT_ENABLED:
    urlpatterns += [path("social/", include("allauth.socialaccount.urls"))]

# Provider urlpatterns, as separate attribute (for reusability).
provider_urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + ".urls")
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns
urlpatterns += provider_urlpatterns
