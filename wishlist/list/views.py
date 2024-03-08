from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Group
from .forms import GroupForm

# Create your views here.
@login_required(login_url="/login")
def home(request):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})

    template = loader.get_template("mainPage.html")
    context = {"user" : request.user, "groups" : groups, "gForm" : gForm}
    return HttpResponse(template.render(context=context, request=request))

@login_required(login_url="/login")
def groupView(request, id, name):
    groups = Group.objects.filter(user=request.user)
    gForm = GroupForm(initial={"user" : request.user})

    template = loader.get_template("groupPage.html")
    context = {"name" : name, "id" : id, "groups" : groups, "gForm" : gForm}
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

# Jobs/requests
def createGroupView(request):
    if(not request.user.is_authenticated):
        return redirect("home")

    if(request.method == "POST"):
        form = GroupForm(request.POST)

        if(form.is_valid()):
            group = form.save()
            return redirect("group", id=group.id, name=group.name)
        else:
            for err in form.errors:
                messages.error(request, form.errors[err])

    return redirect("home")

def deleteGroupView(request):
    if(not request.user.is_authenticated):
        return redirect("home")

    if(request.method=="POST"):
        try:
            id = request.POST.get("groupId")
            g = Group.objects.get(pk = id)
            g.delete()
        except Exception as e:
            print(e)
    return redirect("home")