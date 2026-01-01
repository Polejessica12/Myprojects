from django.contrib import admin
from .models import Customer, UserFooditem, Category, Fooditem

class FooditemInline(admin.TabularInline):
    model = UserFooditem.fooditem.through  # many-to-many intermediate
    extra = 0

class UserFooditemAdmin(admin.ModelAdmin):
    list_display = ['customer', 'meal', 'date_added', 'get_fooditems']
    list_filter = ['meal', 'date_added', 'customer']
    search_fields = ['customer__name']

    def get_fooditems(self, obj):
        return ", ".join([f.name for f in obj.fooditem.all()])
    get_fooditems.short_description = 'Food Items'

admin.site.register(Customer)
admin.site.register(Category)

class FooditemAdmin(admin.ModelAdmin):
    list_display = ['name', 'calories', 'protein', 'fats', 'carbohydrates']
    list_filter = ['category']
    search_fields = ['name']

admin.site.register(Fooditem, FooditemAdmin)
admin.site.register(UserFooditem, UserFooditemAdmin)