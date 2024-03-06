from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("register/", views.register, name="register"),
]