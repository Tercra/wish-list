from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test, name="test"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
]