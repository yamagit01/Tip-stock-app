from django.urls import path

from app import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('tip_create/', views.TipCreate.as_view(), name='tip_create'),
    path('tip_detail/<int:pk>', views.TipDetail.as_view(), name='tip_detail'),
    path('tip_Update/<int:pk>', views.TipUpdate.as_view(), name='tip_update'),
    path('tip_Delete/<int:pk>', views.TipDelete.as_view(), name='tip_delete'),
    path('tip_list/', views.TipList.as_view(), name='tip_list'),
    path('tip_public_list/', views.TipPublicList.as_view(), name='tip_public_list'),
    path('comment/<int:pk>/', views.add_comment, name='add_comment'),
]
