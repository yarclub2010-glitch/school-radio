from django.urls import path

from . import views

urlpatterns = [
    path('', views.playlist, name='playlist'),
    path('upload/', views.upload, name='upload'),
    path('hall/', views.hall, name='hall'),
    path('moderation/', views.moderation, name='moderation'),
    path('api/hall/', views.hall_data, name='hall_data'),
    path('api/hall/played/<int:pk>/', views.hall_played, name='hall_played'),
    path('api/hall/stopped/', views.hall_stopped, name='hall_stopped'),
]
