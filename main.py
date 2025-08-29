import spacy
import os
import requests
import dateparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def get_weather(location, intent, date):
    """
    Fetches current weather data from the OpenWeatherMap API.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "Error: OPENWEATHERMAP_API_KEY not found. Please set it in your .env file."

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "imperial"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10) # 10-second timeout
        response.raise_for_status()
        data = response.json()

        if intent == "temperature":
            temp = data['main']['temp']
            return f"The current temperature in {location} is {temp}°F."
        elif intent == "humidity":
            humidity = data['main']['humidity']
            return f"The current humidity in {location} is {humidity}%."
        elif intent == "wind speed":
            wind_speed = data['wind']['speed']
            return f"The current wind speed in {location} is {wind_speed} mph."
        else: # Default to current weather
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"The current weather in {location} is {weather_desc} with a temperature of {temp}°F."

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {e}"
    except KeyError:
        return f"Could not find weather data for {location}. Please check the location name."

def get_forecast(location, date):
    """
    Fetches 5-day weather forecast data from the OpenWeatherMap API.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "Error: OPENWEATHERMAP_API_KEY not found. Please set it in your .env file."

    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": location,
        "appid": api_key,
        "units": "imperial"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10) # 10-second timeout
        response.raise_for_status()
        data = response.json()

        forecasts = data['list']
        target_forecasts = []
        for forecast in forecasts:
            forecast_date = datetime.fromtimestamp(forecast['dt'])
            if forecast_date.date() == date.date():
                target_forecasts.append(forecast)
        
        if not target_forecasts:
            return f"No forecast data available for {location} on {date.strftime('%Y-%m-%d')}."

        summary = f"Forecast for {location} on {date.strftime('%A, %B %d')}:\n"
        for forecast in target_forecasts:
            time = datetime.fromtimestamp(forecast['dt']).strftime('%I:%M %p')
            weather_desc = forecast['weather'][0]['description']
            temp = forecast['main']['temp']
            summary += f"- {time}: {weather_desc.capitalize()}, {temp}°F\n"
        
        return summary

    except requests.exceptions.RequestException as e:
        return f"Error fetching forecast data: {e}"
    except KeyError:
        return f"Could not find forecast data for {location}. Please check the location name."


def process_question(question):
    """
    Processes the user's question to extract location, intent, and date.
    """
    doc = nlp(question)

    location = None
    for ent in doc.ents:
        if ent.label_ == "GPE":
            location = ent.text
            break
    
    if not location:
        for chunk in doc.noun_chunks:
             if "in" in chunk.root.head.text or "for" in chunk.root.head.text:
                 location = chunk.text
                 break

    if not location:
        return "Could not determine the location from your question.", None, None

    date_entity = None
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_entity = ent.text
            break
    
    target_date = datetime.now()
    if date_entity:
        parsed_date = dateparser.parse(date_entity, settings={'PREFER_DATES_FROM': 'future'})
        if parsed_date:
            target_date = parsed_date

    intent = "current weather"
    if "temperature" in question.lower():
        intent = "temperature"
    elif "humidity" in question.lower():
        intent = "humidity"
    elif "wind" in question.lower():
        intent = "wind speed"
    elif "forecast" in question.lower() or (date_entity and target_date.date() > datetime.now().date()):
        intent = "forecast"

    now = datetime.now()
    if target_date.date() < now.date():
        return location, "past_weather", target_date
    elif target_date.date() > now.date() or intent == "forecast":
        if target_date.date() > (now + timedelta(days=5)).date():
             return location, "future_weather_limit", target_date
        return location, "forecast", target_date
    else:
        return location, intent, now


def main():
    """
    Main function to run the weather AI bot in the console.
    """
    print("Hello! I am a weather bot. Ask me a question about the weather.")
    print("For example: 'What is the temperature in London?' or 'Tell me the forecast for New York.'")
    
    while True:
        question = input("> ")
        if question.lower() in ["exit", "quit"]:
            break

        location, intent, date = process_question(question)

        response = ""
        if intent == "past_weather":
            response = "I'm sorry, but I cannot retrieve historical weather data with the current plan."
        elif intent == "future_weather_limit":
            response = f"I can only provide a 5-day forecast. {date.strftime('%Y-%m-%d')} is too far in the future."
        elif location and intent:
            if intent == 'forecast':
                response = get_forecast(location, date)
            else:
                response = get_weather(location, intent, date)
        else:
            response = location # Contains the error message from process_question

        print(response)

if __name__ == "__main__":
    main()
