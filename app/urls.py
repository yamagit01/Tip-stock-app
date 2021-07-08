from django.urls import path

from app import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('tip_create/', views.TipCreateView.as_view(), name='tip_create'),
    path('tip_detail/<int:pk>', views.TipDetailView.as_view(), name='tip_detail'),
    path('tip_update/<int:pk>', views.TipUpdateView.as_view(), name='tip_update'),
    path('tip_delete/<int:pk>', views.TipDeleteView.as_view(), name='tip_delete'),
    path('tip_list/', views.TipListView.as_view(), name='tip_list'),
    path('tip_public_list/', views.TipListView.as_view(), name='tip_public_list'),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:pk>/<int:comment_no>', views.delete_comment, name='delete_comment'),
    path('add_like/<int:pk>/', views.add_like, name='add_like'),
    path('delete_like/<int:pk>/', views.delete_like, name='delete_like'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('thanks/', views.ThanksView.as_view(), name='thanks'),
    path('notifications/', views.notifications, name='notifications'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('policy/', views.PolicyView.as_view(), name='policy'),
    path('usertip/<int:id>/', views.UserTipView.as_view(), name='usertip'),
]
