import requests

NUTRITIONIX_APP_ID = 'your_app_id'
NUTRITIONIX_API_KEY = 'your_api_key'

def fetch_food_data(food_name):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": "afb51250",
        "x-app-key": "0809a52a71d47ae6f482ad174a475269",
        "Content-Type": "application/json",
    }
    data = {
        "query": food_name
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    return None