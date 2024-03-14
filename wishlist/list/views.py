from http.client import HTTPResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Group, Item, ItemData
from .forms import GroupForm
from .productInfo import scrapeInfo
from django.conf import settings
import os

# Create your views here.
@login_required(login_url="/login")
def home(request):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})

    template = loader.get_template("mainPage.html")
    context = {"MEDIA_URL": settings.MEDIA_URL, "user" : request.user, "groups" : groups, "gForm" : gForm}
    return HttpResponse(template.render(context=context, request=request))

@login_required(login_url="/login")
def groupView(request, id, name):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})
    items = Item.objects.filter(group__id=id)

    template = loader.get_template("groupPage.html")
    context = {"MEDIA_URL": settings.MEDIA_URL, "name" : name, "id" : id, "groups" : groups, "gForm" : gForm, "items" : items}
    return HttpResponse(template.render(context=context, request=request))

def loginView(request):
    # If the user is already logged in
    if request.user.is_authenticated:
        return redirect("home")

    if(request.method == "POST"):
        username = request.POST.get("user")
        password = request.POST.get("pass")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid login")
        
    template = loader.get_template('loginRegister.html')
    context = {"page" : "Login"}
    return HttpResponse(template.render(context=context, request=request))

def logoutView(request):
    logout(request)
    return redirect("login")

def register(request):
    if(request.method == "POST"):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
        else:
            for err in form.errors:
                messages.error(request, form.errors[err])
    else:
        form = UserCreationForm()

    template = loader.get_template('loginRegister.html')
    context = {"page" : "Register", "form" : form}
    return HttpResponse(template.render(context=context, request=request))

# Handles creating a group
def createGroupView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method == "POST"):
        form = GroupForm(request.POST)

        if(form.is_valid()):
            group = form.save()
            return redirect("group", id=group.id, name=group.name)
        else:
            for err in form.errors:
                messages.error(request, form.errors[err])

    return redirect("home")

# Handles Deleting a group
def deleteGroupView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method=="POST"):
        try:
            id = request.POST.get("groupId")
            images = [x["imagePath"] for x in Item.objects.filter(group=id).values()]
            g = Group.objects.get(pk = id)
            g.delete()

            # Delete images of items that do not use that image path anymore (maybeChangeInProduction)
            other = [x["imagePath"] for x in Item.objects.filter(imagePath__in=images).values()]
            other = set(images).difference(other)
            for o in other:
                os.remove(os.path.join(settings.MEDIA_ROOT, o))

        except Exception as e:
            print(e)
    return redirect("home")

# Handles the addition of a new item
def addItemView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method=="POST"):
        url = request.POST.get("url")
        groupId = request.POST.get("groupId")
        groupName = request.POST.get("groupName")
        temp = scrapeInfo(url)
        if(temp["success"] == True):
            temp = temp["res"]

            item = Item.objects.create(user=request.user, group_id=groupId, name=temp["name"], imagePath=temp["img"])
            # item.save()
            itemData = ItemData(item=item, price=temp["price"], currency=temp["currency"], inStock=temp["inStock"], webLink=temp["url"])
            itemData.save()
        else:
            messages.error(request, temp["msg"])

        return redirect("group", id=groupId, name=groupName)


    return redirect("home")

# Handles the deletion of an item
def deleteItemsView(request):
    if(not request.user.is_authenticated):
        return redirect("login")
    
    if(request.method=="POST"):
        groupId = request.POST.get("groupId")
        groupName = request.POST.get("groupName")
        selectedItems = request.POST.getlist("selectedItems")
        items = Item.objects.filter(pk__in=selectedItems)
        images = [x["imagePath"] for x in items.values()]
        items.delete()

        # Delete images of items that do not use that image path anymore (maybeChangeInProduction)
        other = [x["imagePath"] for x in Item.objects.filter(imagePath__in=images).values()]
        other = set(images).difference(other)
        for o in other:
            os.remove(os.path.join(settings.MEDIA_ROOT, o))
            

        return redirect("group", id=groupId, name=groupName)

    return redirect("home")