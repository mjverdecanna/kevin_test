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
        "units": "imperial"  # Use imperial units
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
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
        elif intent == "current weather":
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"The current weather in {location} is {weather_desc} with a temperature of {temp}°F."
        elif intent == "forecast":
            # The free API tier doesn't provide a multi-day forecast in the 'weather' endpoint.
            # This would require a different endpoint or a more advanced plan.
            # For now, we can give the current weather as a form of "forecast".
            weather_desc = data['weather'][0]['description']
            return f"The current forecast for {location} is: {weather_desc}."
        else:
            return "I can't provide that information yet."

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
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Find the forecast for the target date
        forecasts = data['list']
        target_forecasts = []
        for forecast in forecasts:
            forecast_date = datetime.fromtimestamp(forecast['dt'])
            if forecast_date.date() == date.date():
                target_forecasts.append(forecast)
        
        if not target_forecasts:
            return f"No forecast data available for {location} on {date.strftime('%Y-%m-%d')}."

        # Summarize the forecast for the day
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
        if ent.label_ == "GPE":  # Geopolitical Entity
            location = ent.text
            break
    
    if not location:
        # Fallback for locations not recognized as GPE
        for chunk in doc.noun_chunks:
             if "in" in chunk.root.head.text or "for" in chunk.root.head.text:
                 location = chunk.text
                 break

    if not location:
        return "Could not determine the location from your question.", None, None

    # Date and Time extraction
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

    # Intent detection
    intent = "current weather" # Default intent
    if "temperature" in question.lower():
        intent = "temperature"
    elif "humidity" in question.lower():
        intent = "humidity"
    elif "wind" in question.lower():
        intent = "wind speed"
    elif "forecast" in question.lower() or (date_entity and target_date.date() > datetime.now().date()):
        intent = "forecast"

    # Distinguish between past, present, and future
    now = datetime.now()
    if target_date.date() < now.date():
        return location, "past_weather", target_date
    elif target_date.date() > now.date() or intent == "forecast":
        # Check if the forecast is within the 5-day limit
        if target_date.date() > (now + timedelta(days=5)).date():
             return location, "future_weather_limit", target_date
        return location, "forecast", target_date
    else: # Current weather
        return location, intent, now


def get_weather_response(question):
    """
    Takes a user's question as a string and returns the weather response.
    This function encapsulates the core logic.
    """
    location, intent, date = process_question(question)

    if intent == "past_weather":
        return "I'm sorry, but I cannot retrieve historical weather data with the current plan."
    
    if intent == "future_weather_limit":
        return f"I can only provide a 5-day forecast. {date.strftime('%Y-%m-%d')} is too far in the future."

    if location and intent:
        if intent == 'forecast':
            return get_forecast(location, date)
        else:
            return get_weather(location, intent, date)
    else:
        # This part of the original logic was returning a tuple.
        # Let's return a user-friendly string instead.
        if location:
             return "Sorry, I could understand the location but not the rest of your question. Please try again."
        else:
             return "Sorry, I couldn't understand your question. Please try again."


def main_console():
    """
    Main function to run the weather AI bot in the console.
    """
    print("Hello! I am a weather bot. Ask me a question about the weather.")
    print("For example: 'What is the temperature in London?' or 'Tell me the forecast for New York.'")
    
    while True:
        question = input("> ")
        if question.lower() in ["exit", "quit"]:
            break

        response = get_weather_response(question)
        print(response)

if __name__ == "__main__":
    main_console()
