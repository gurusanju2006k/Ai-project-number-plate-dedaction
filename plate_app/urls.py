from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('detect/', views.detect_plate, name='detect'),
    path('history/', views.history, name='history'),
    path('register/', views.register_view),
    path("live/", views.detect_frame),
    path("process_frame/", views.process_frame),
]