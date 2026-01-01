from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import *
from .filters import fooditemFilter
from .decorators import *
from .utils import fetch_food_data

# ---------------- Admin Home ---------------- #

@login_required(login_url='login')
@admin_only

def home(request):
    customers = Customer.objects.all()
    selected_customer_id = request.GET.get('customer_id')
    selected_customer = None
    user_data = {'breakfast': [], 'lunch': [], 'dinner': [], 'snacks': []}

    if selected_customer_id:
        try:
            selected_customer = Customer.objects.get(id=selected_customer_id)
            user_logs = UserFooditem.objects.filter(customer=selected_customer).prefetch_related('fooditem')

            for log in user_logs:
                for food in log.fooditem.all():
                    user_data[log.meal].append(food)
        except Customer.DoesNotExist:
            selected_customer = None

    context = {
        'customers': customers,
        'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
        'user_data': user_data,
        'selected_customer': selected_customer,  # ✅ added here
    }
    return render(request, 'main.html', context)
# ---------------- Admin Food Items ---------------- #

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def fooditem(request):
    def get_category_items(name):
        category = Category.objects.filter(name=name).first()
        return category.fooditem_set.all() if category else []

    breakfast = get_category_items('breakfast')
    lunch = get_category_items('lunch')
    dinner = get_category_items('dinner')
    snacks = get_category_items('snacks')

    context = {
        'breakfast': breakfast, 'bcnt': len(breakfast),
        'lunch': lunch, 'lcnt': len(lunch),
        'dinner': dinner, 'dcnt': len(dinner),
        'snacks': snacks, 'scnt': len(snacks)
    }
    return render(request, 'fooditem.html', context)

# ---------------- Create Food Item (with Nutrition API) ---------------- #

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def createfooditem(request):
    if request.method == 'POST':
        food_name = request.POST.get('food_name')

        if not food_name:
            messages.error(request, "Food name is required.")
            return redirect('createfooditem')
        existing = Fooditem.objects.filter(name__iexact=food_name).first()
        if existing:
            messages.info(request, f"'{existing.name}' already exists in the database.")
            return redirect('fooditem')

        result = fetch_food_data(food_name)

        if result:
            try:
                food = result['foods'][0]  # Safely get first item
                item = Fooditem.objects.create(
                    name=food.get('food_name'),
                    carbohydrates=food.get('nf_total_carbohydrate', 0),
                    fats=food.get('nf_total_fat', 0),
                    protein=food.get('nf_protein', 0),
                    calories=food.get('nf_calories', 0),
                    quantity=food.get('serving_qty', 1)
                )
                item.save()
                messages.success(request, f"Food item '{item.name}' added successfully!")
                return redirect('fooditem')
            except Exception as e:
                messages.error(request, f"Error processing food data: {str(e)}")
        else:
            messages.error(request, "Failed to fetch nutrition info from API.")

    return render(request, 'createfooditem.html')
# ---------------- Register ---------------- #

@unauthorized_user

def registerPage(request):
    form = createUserForm()

    if request.method == 'POST':
        form = createUserForm(request.POST)

        if form.is_valid():
            try:
                # Create user
                user = form.save()

                # Get or create the 'user' group
                group, created = Group.objects.get_or_create(name='users')
                user.groups.add(group)

                # Create Customer profile
                Customer.objects.create(
                    user=user,
                    name=form.cleaned_data.get('username'),
                    email=form.cleaned_data.get('email')
                )

                messages.success(request, f'Account created for {user.username}')
                return redirect('login')

            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors in the form.')

    return render(request, 'register.html', {'form': form})
# ---------------- Login ---------------- #

@unauthorized_user
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.warning(request, 'Invalid username or password.')
    return render(request, 'login.html')

# ---------------- Logout ---------------- #

@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')

# ---------------- User Page ---------------- #

from django.contrib.auth.decorators import login_required
from .decorators import allowed_users
import datetime
from .models import UserFooditem, Fooditem
from .filters import fooditemFilter

@login_required(login_url='login')
@allowed_users(['users'])
def userPage(request):
    customer = request.user.customer
    today = datetime.date.today()
    all_user_fooditems = UserFooditem.objects.filter(customer=customer, date_added=today)

    def get_meal_items(meal):
        return [food for uf in all_user_fooditems.filter(meal=meal) for food in uf.fooditem.all()]

    meals = ['breakfast', 'lunch', 'dinner', 'snacks']
    meal_data = {}
    totalCalories = 0
    totalMacros = {'carbohydrates': 0, 'fats': 0, 'protein': 0}

    for meal in meals:
        items = get_meal_items(meal)
        meal_data[meal] = items
        for food in items:
            totalCalories += food.calories
            totalMacros['carbohydrates'] += food.carbohydrates
            totalMacros['fats'] += food.fats
            totalMacros['protein'] += food.protein

    CalorieLeft = 2000 - totalCalories
    progress = (totalCalories / 2000) * 100 if totalCalories else 0

    # Macro labels to iterate in template
    macro_labels = [
        ('carbohydrates', 'Carbs'),
        ('fats', 'Fats'),
        ('protein', 'Protein')
    ]

    # Macro recommended daily limits (grams)
    macro_limits = {
        'carbohydrates': 275,
        'fats': 80,
        'protein': 100,
    }

    # Convert totalMacros dict to flat context variables (for template use without filters)
    macro_values = {}
    for key, label in macro_labels:
        value = totalMacros.get(key, 0)
        limit = macro_limits.get(key, 1)
        percent = min(max(round((value / limit) * 100), 0), 100)
        macro_values[f'{key}_value'] = value
        macro_values[f'{key}_limit'] = limit
        macro_values[f'{key}_width'] = f"w-[{percent}%]"

    context = {
        'CalorieLeft': CalorieLeft,
        'totalCalories': totalCalories,
        'cnt': sum(len(meal_data[meal]) for meal in meals),
        'meal_data': meal_data,
        'fooditem': Fooditem.objects.all(),
        'myfilter': fooditemFilter(request.GET, queryset=Fooditem.objects.all()),
        'progress': progress,
        'totalMacros': totalMacros,
        'macro_labels': macro_labels,
        **macro_values,
    }

    return render(request, 'user.html', context)

# ---------------- Add Food to User ---------------- #

@login_required(login_url='login')
@allowed_users(['users'])
def addFooditem(request):
    customer = request.user.customer
    available_fooditems = Fooditem.objects.all()

    if request.method == 'POST':
        selected_ids = request.POST.getlist('fooditem_ids')
        meal = request.POST.get('meal')

        if selected_ids and meal:
            for fid in selected_ids:
                try:
                    food = Fooditem.objects.get(id=fid)
                    # Create a new UserFooditem for each food and meal
                    UserFooditem.objects.create(
                        customer=customer,
                        meal=meal,
                        date_added=datetime.date.today()
                    ).fooditem.add(food)
                except Fooditem.DoesNotExist:
                    messages.warning(request, f"Food item with ID {fid} not found.")
            messages.success(request, f"Food items added to your {meal} log.")
        else:
            messages.warning(request, "Please select food items and a meal category.")

        return redirect('userPage')

    context = {'fooditems': available_fooditems}
    return render(request, 'addUserFooditem.html', context)