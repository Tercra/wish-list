from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Create your views here.
def test(request):
    return HttpResponse("Hello world!")

def login(request):
    if(request.method == "POST"):
        pass
    template = loader.get_template('loginRegister.html')
    context = {"page" : "login"}
    return HttpResponse(template.render(context=context, request=request))

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
    context = {"page" : "register", "form" : form}
    return HttpResponse(template.render(context=context, request=request))
