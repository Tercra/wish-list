from django.contrib import admin
from .models import Group, Item, ItemData

class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name",)

class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group", "name", "imagePath",)

class ItemDataAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "price", "currency", "inStock", "webLink")

# Register your models here.
admin.site.register(Group, GroupAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemData, ItemDataAdmin)