from django.db import models
from django.contrib.auth.models import User
import datetime

# Create your models here.

# Our models will store:
    # 1.Customers
    # 2.All available food items
    # 3.Category of food items we offer
    # 4.Consumed food items

class Customer(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    options = (
        ('breakfast', 'breakfast'),
        ('lunch','lunch'),
        ('snacks', 'snacks'),
        ('dinner','dinner')
        
    )
    name = models.CharField(max_length=200, choices=options) 
    
    def __str__(self):
        return self.name

class Fooditem(models.Model):
    name = models.CharField(max_length=200)
    category = models.ManyToManyField(Category)
    carbohydrates = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    fats = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    protein = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    calories = models.DecimalField(max_digits=5, decimal_places=2, default=2, blank=True)
    quantity = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return self.name

class UserFooditem(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    fooditem = models.ManyToManyField(Fooditem)
    meal = models.CharField(max_length=50, choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
         ('snacks', 'Snacks'),
        ('dinner', 'Dinner')
    ])
    date_added = models.DateField(default=datetime.date.today)