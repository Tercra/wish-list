from django.contrib import admin
from .models import Group

class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name",)
# Register your models here.
admin.site.register(Group, GroupAdmin)