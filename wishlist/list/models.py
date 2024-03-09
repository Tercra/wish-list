from locale import currency
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Group(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    imagePath = models.CharField(max_length=255)

class ItemData(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits= 10, decimal_places=2)
    currency = models.CharField(max_length=3)
    inStock = models.BooleanField()
    webLink = models.CharField(max_length=255)