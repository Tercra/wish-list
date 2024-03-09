from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("register/", views.register, name="register"),
    path("group/<int:id>/<str:name>", views.groupView, name="group"),
    path("createGroup/", views.createGroupView, name="createGroup"),
    path("deleteGroup/", views.deleteGroupView, name="deleteGroup"),
    path("addItem/", views.addItemView, name="addItem"),
]