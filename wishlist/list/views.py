from http.client import HTTPResponse
import re
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
from .updateInfo import updateInfo, scrapeInfoDatas
from django.conf import settings
import os
from asgiref.sync import async_to_sync

# Create your views here.
@login_required(login_url="/login")
def searchPage(request):
    items = Item.objects.filter(user=request.user)

    if(request.method == "POST"):
        searchText = request.POST.get("searchText")
        selectFilter = request.POST.get("selectFilter")
        items = items.filter(name__icontains=searchText)
        if(selectFilter != ""):
            items = items.filter(idatas__origin=selectFilter)
    
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})

    template = loader.get_template("searchPage.html")
    context = {"MEDIA_URL": settings.MEDIA_URL, "user" : request.user, "groups" : groups, "gForm" : gForm, "items" : items}
    return HttpResponse(template.render(context=context, request=request))

@login_required(login_url="/login")
def groupView(request, id, name):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})
    items = Item.objects.filter(group__pk=id)

    template = loader.get_template("groupPage.html")
    context = {"MEDIA_URL": settings.MEDIA_URL, "name" : name, "id" : id, "groups" : groups, "gForm" : gForm, "items" : items}
    return HttpResponse(template.render(context=context, request=request))

@login_required(login_url="/login")
def itemView(request, id):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})
    item = Item.objects.select_related("group").get(pk=id)
    itemDatas = ItemData.objects.filter(item__pk=id)

    template = loader.get_template("itemPage.html")
    context = {"MEDIA_URL": settings.MEDIA_URL, "id" : id, "groups" : groups, "gForm" : gForm, "item" : item, "itemDatas" : itemDatas}
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
            groupId = request.POST.get("groupId")
            images = [x["imagePath"] for x in Item.objects.filter(group=groupId).values()]
            g = Group.objects.get(pk = groupId)
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
            itemData = ItemData.objects.create(item=item, price=temp["price"], currency=temp["currency"], inStock=temp["inStock"], webLink=temp["url"], origin=temp["origin"])
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
        selectedItems = request.POST.getlist("itemId")
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

# Handles moving items to another group
def moveItemsView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method=="POST"):
        groupId = request.POST.get("groupId")
        groupName = request.POST.get("groupName")
        moveId = request.POST.get("moveGroups")
        selectedItems = request.POST.getlist("itemId")

        newGroup = Group.objects.get(pk=moveId)
        Item.objects.filter(pk__in=selectedItems).update(group=newGroup)

        return redirect("group", id=groupId, name=groupName)


    return redirect("home")

# Handles updating item when adding a link to the item
def updateItemView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method == "POST"):
        itemId = request.POST.get("itemId")
        url = request.POST.get("itemURL")
        temp = updateInfo(url)
        if(temp["success"] == True):
            temp = temp["res"]

            item = Item.objects.get(pk=itemId)
            relatedData = ItemData.objects.filter(item=item, origin=temp["origin"])
            if(relatedData.exists()):
                relatedData.update(webLink=temp["url"], price=temp["price"], currency=temp["currency"], inStock=temp["inStock"])
            else:
                ItemData.objects.create(item=item, price=temp["price"], currency=temp["currency"], inStock=temp["inStock"], webLink=temp["url"], origin=temp["origin"])

        else:
            messages.error(request, temp["msg"])

        return redirect("itemPage", id=itemId)

    return redirect("home")

# Handles Updating all the data an item has
def updateItemDataView(request):
    if(not request.user.is_authenticated):
        return redirect("login")

    if(request.method == "POST"):
        itemId = request.POST.get("itemId")
        itemDatas = ItemData.objects.filter(item__pk=itemId)

        sync_get_data = async_to_sync(scrapeInfoDatas)

        itemDataUpdated = sync_get_data([item.webLink for item in itemDatas])

        for index, (item, scrapeResult) in enumerate(zip(itemDatas, itemDataUpdated)):
            if(scrapeResult["success"] == True):
                temp = scrapeResult["res"]
                item.price = temp["price"]
                item.currency = temp["currency"]
                item.inStock = temp["inStock"]
                item.webLink = temp["url"]
            else:
                messages.error(request, temp["msg"])

        ItemData.objects.bulk_update(itemDatas, ["price", "currency", "inStock", "webLink"])

        return redirect("itemPage", id=itemId)

    return redirect("home")