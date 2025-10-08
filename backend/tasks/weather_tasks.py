import requests
import os
from backend.celery_app import celery_app
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

# Get API key from environment
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

@celery_app.task
def execute_weather_task(task_args):
    try:
        query = task_args.get('query', '').lower()
        
        # Extract location from query
        location = extract_location(query)
        
        if location == "your area":
            return "🌤️ Please specify a city name. Example: 'weather in London' or 'forecast for Tokyo'"
        
        # Get real weather data
        weather_info = get_real_weather(location)
        
        if weather_info:
            return weather_info
        else:
            # Fallback to mock data if API fails
            return get_mock_weather(location, "🔍 Weather service temporarily unavailable")
        
    except Exception as e:
        return f"❌ Weather task error: {str(e)}"

def get_real_weather(location):
    """Get real weather data from OpenWeatherMap API"""
    try:
        # Use the simple current weather API (proven to work)
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        print(f"🌤️ Fetching weather for: {location}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract weather information
            city_name = data['name']
            country = data['sys']['country']
            temp_c = data['main']['temp']
            temp_f = (temp_c * 9/5) + 32
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            description = data['weather'][0]['description'].title()
            feels_like = data['main']['feels_like']
            pressure = data['main']['pressure']
            
            location_display = f"{city_name}, {country}"
            
            print(f"✅ Successfully fetched weather for: {location_display}")
            
            return f"""🌤️ Weather in {location_display}:

🌡️ Temperature: {temp_c:.1f}°C / {temp_f:.1f}°F
🤔 Feels like: {feels_like:.1f}°C / {(feels_like * 9/5) + 32:.1f}°F
💧 Humidity: {humidity}%
💨 Wind: {wind_speed} m/s
📊 Pressure: {pressure} hPa
☁️ Conditions: {description}"""
        
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"⏰ API timeout for: {location}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"🔌 API connection error for: {location}")
        return None
    except Exception as e:
        print(f"❌ API error for {location}: {e}")
        return None

def get_mock_weather(location, reason="🔍 Weather service unavailable"):
    """Fallback mock weather data"""
    import random
    import hashlib
    
    location_hash = int(hashlib.md5(location.lower().encode()).hexdigest()[:8], 16)
    random.seed(location_hash)
    
    tropical_locations = ["mumbai", "delhi", "miami", "bangkok", "singapore", "dubai", "mexico", "rio", "bangalore", "chennai", "kolkata", "hyderabad"]
    cold_locations = ["moscow", "oslo", "helsinki", "stockholm", "ottawa", "anchorage", "warsaw", "prague", "berlin"]
    coastal_locations = ["mumbai", "miami", "tokyo", "sydney", "london", "san francisco", "vancouver"]
    
    if any(loc in location.lower() for loc in tropical_locations):
        temp_c = random.randint(25, 38)
        conditions = ["Sunny", "Partly Cloudy", "Humid", "Hot", "Clear"]
    elif any(loc in location.lower() for loc in cold_locations):
        temp_c = random.randint(-10, 15)
        conditions = ["Cloudy", "Snowy", "Cold", "Windy", "Overcast"]
    elif any(loc in location.lower() for loc in coastal_locations):
        temp_c = random.randint(15, 28)
        conditions = ["Partly Cloudy", "Breezy", "Clear", "Mild", "Windy"]
    else:
        temp_c = random.randint(10, 25)
        conditions = ["Sunny", "Cloudy", "Clear", "Mild", "Partly Cloudy"]
    
    temp_f = (temp_c * 9/5) + 32
    condition = random.choice(conditions)
    humidity = random.randint(30, 85)
    wind_speed = random.uniform(1.0, 15.0)
    
    return f"""🌤️ Weather in {location.title()}:

🌡️ Temperature: {temp_c}°C / {temp_f:.1f}°F
💧 Humidity: {humidity}%
💨 Wind: {wind_speed:.1f} m/s
☁️ Conditions: {condition}

{reason}."""

def extract_location(query):
    """Extract location from weather query"""
    import re
    
    patterns = [
        r'weather in\s+(.+)',
        r'weather at\s+(.+)',
        r'weather for\s+(.+)',
        r'forecast for\s+(.+)',
        r'temperature in\s+(.+)',
        r'humidity in\s+(.+)',
        r'climate in\s+(.+)',
        r'how is weather in\s+(.+)',
        r"what's the weather in\s+(.+)",
        r'what is the weather in\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            location = re.sub(r'[?.!]$', '', location)
            return location
    
    if any(word in query for word in ['weather', 'forecast', 'temperature', 'humidity']):
        return "your area"
    
    return "your area"