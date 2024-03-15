from django.urls import path
from . import views

urlpatterns = [
    path('', views.searchPage, name="home"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("register/", views.register, name="register"),
    path("group/<int:id>/<str:name>", views.groupView, name="group"),
    path("item/<int:id>", views.itemView, name="itemPage"),
    path("createGroup/", views.createGroupView, name="createGroup"),
    path("deleteGroup/", views.deleteGroupView, name="deleteGroup"),
    path("addItem/", views.addItemView, name="addItem"),
    path("deleteItems/", views.deleteItemsView, name="deleteItems"),
    path("moveItems/", views.moveItemsView, name="moveItems"),
    path("updateItem/", views.updateItemView, name="updateItem"),
]