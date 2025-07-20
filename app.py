from flask import Flask, render_template, request
import requests
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["weather_db"]
collection = db["weather_history"]

# OpenWeatherMap API
API_KEY = "ed4ea65d163f3dff2d492c3e59804e7f"

# ---------- Function to get coordinates ----------
def get_coordinates(city):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    response = requests.get(geo_url)
    data = response.json()

    if data and isinstance(data, list) and len(data) > 0:
        result = data[0]
        returned_name = result.get('name', '').lower()
        input_name = city.lower()

        # If user typed "India", returned_name will also be "India" — skip such results
        # Only accept if user input ≠ country name or state name
        if returned_name == input_name and len(input_name) > 3:
            # Further filter out countries by checking if it's a country code match
            if result.get('country', '').lower() != input_name:
                lat = result['lat']
                lon = result['lon']
                city_name = result['name']
                country = result['country']
                return lat, lon, f"{city_name}, {country}"

    return None, None, None


# ---------- Function to fetch weather ----------
def get_weather_data(lat, lon):
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(weather_url)
    data = response.json()

    if response.status_code == 200 and "main" in data:
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
        }
    return None

# ---------- Home Route ----------
@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error_message = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if city:
            lat, lon, full_city_name = get_coordinates(city)

            if lat is None or lon is None:
                error_message = f"❌ '{city}' is not a valid city name."
            else:
                weather_data = get_weather_data(lat, lon)
                if weather_data:
                    document = {
                        "city": full_city_name,
                        "temperature": weather_data["temperature"],
                        "humidity": weather_data["humidity"],
                        "description": weather_data["description"],
                        "timestamp": datetime.now()
                    }
                    collection.insert_one(document)
        else:
            error_message = "❌ Please enter a city name."

    history = list(collection.find().sort("timestamp", -1).limit(5))
    return render_template("index.html", weather=weather_data, history=history, error=error_message)

# ---------- History Route ----------
@app.route("/history")
def history():
    history = list(collection.find().sort("timestamp", -1))
    return render_template("history.html", history=history)

# ---------- Run the App ----------
if __name__ == "__main__":
    app.run(debug=True)
