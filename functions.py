from dotenv import load_dotenv
import os
import requests
from typing import Optional

# Load environment variables from the .env file
load_dotenv()

WEATHER_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
default_location_coordinates = (37.7790262, -122.419906)
default_units = 'F'

def get_location_coordinates(location: str) -> Optional[tuple[float, float]]:
	"""
	Private function to get coordinates for a location using OpenWeather's geocoding API.
	
	Args:
		location (str): Freeform location string (e.g., "London", "New York, US")
	
	Returns:
		Optional[tuple[float, float]]: Tuple of (latitude, longitude) if found, None if not found
	"""
	GEOCODING_URL = 'http://api.openweathermap.org/geo/1.0/direct'
	
	params = {
		'q': location,
		'limit': 1,
		'appid': WEATHER_API_KEY
	}
	
	try:
		response = requests.get(GEOCODING_URL, params=params)
		response.raise_for_status()
		data = response.json()
		
		if data:
			return (data[0]['lat'], data[0]['lon'])
		return None
		
	except requests.exceptions.RequestException as e:
		raise Exception(f"Error getting location coordinates: {str(e)}")

def get_current_weather_latlong(latlong: tuple[float, float] = default_location_coordinates, unit: str = default_units) -> dict:
	"""
	Fetch current weather for a specified location.
	
	Args:
		location (tuple): (lat, long) of the location to fetch weather for
		unit (str): Temperature unit, 'C' for Celsius or 'F' for Fahrenheit
	
	Returns:
		dict: Weather data including temperature, description, and humidity
	"""
	BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
	
	# Convert unit parameter to API format
	units = 'imperial' if unit.upper() == 'F' else 'metric'
	
	# Make API request
	params = {
		'lat': latlong[0],
		'lon': latlong[1],
		'appid': WEATHER_API_KEY,
		'units': units
	}
	
	try:
		response = requests.get(BASE_URL, params=params)
		response.raise_for_status()
		return response.json()
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 401:
			raise Exception("Invalid API key. Please check your OpenWeatherMap API key in the .env file")
		elif e.response.status_code == 404:
			raise Exception(f"Latlong {latlong} not found")
		else:
			raise Exception(f"HTTP error occurred: {str(e)}")
	except requests.exceptions.ConnectionError:
		raise Exception("Failed to connect to weather service. Please check your internet connection")
	except requests.exceptions.Timeout:
		raise Exception("Request timed out. Please try again")
	except requests.exceptions.RequestException as e:
		raise Exception(f"An error occurred while fetching weather data: {str(e)}")
	except KeyError as e:
		raise Exception(f"Unexpected response format from weather service: {str(e)}")

def get_current_weather_city(location: str, unit: str = default_units) -> dict:
	"""
	Fetch current weather for a specified location by city name

	Args:
		location (str): City name (e.g., "London", "New York, US", "San Francisco, CA")
		unit (str): Temperature unit, 'C' for Celsius or 'F' for Fahrenheit
	
	Returns:
		dict: Weather data including temperature, description, and humidity
	"""
	latlong = get_location_coordinates(location)
	return get_current_weather_latlong(latlong, unit)

def get_hourly_weather_forecast_latlong(latlong: tuple[float, float] = default_location_coordinates, unit: str = default_units) -> dict:
	"""
	Fetches the hourly weather forecast over 48 hours for a specified location.
	
	Args:
		latlong (tuple): (lat, long) of the location to fetch forecast for
		unit (str): Temperature unit, 'C' for Celsius or 'F' for Fahrenheit
	
	Returns:
		dict: Weather forecast data including hourly temperatures, descriptions, and humidity
	"""
	FORECAST_URL = 'https://api.openweathermap.org/data/3.0/onecall'
	
	# Convert unit parameter to API format
	units = 'imperial' if unit.upper() == 'F' else 'metric'
	
	params = {
		'lat': latlong[0],
		'lon': latlong[1],
		'appid': WEATHER_API_KEY,
		'units': units,
		'exclude': 'current,minutely,daily,alerts'  # Only get hourly data
	}
	
	try:
		response = requests.get(FORECAST_URL, params=params)
		response.raise_for_status()
		return response.json()
		
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 401:
			raise Exception("Invalid API key. Please check your OpenWeatherMap API key in the .env file")
		elif e.response.status_code == 404:
			raise Exception(f"Latlong {latlong} not found")
		else:
			raise Exception(f"HTTP error occurred: {str(e)}")
	except requests.exceptions.ConnectionError:
		raise Exception("Failed to connect to weather service. Please check your internet connection")
	except requests.exceptions.Timeout:
		raise Exception("Request timed out. Please try again")
	except requests.exceptions.RequestException as e:
		raise Exception(f"An error occurred while fetching forecast data: {str(e)}")
	except KeyError as e:
		raise Exception(f"Unexpected response format from weather service: {str(e)}")

def get_hourly_weather_forecast_city(location: str, unit: str = default_units) -> dict:
	"""
	Fetches the hourly weather forecast over 48 hours for a specified location by city name.
	"""
	latlong = get_location_coordinates(location)
	return get_hourly_weather_forecast_latlong(latlong, unit)

def get_5_day_weather_forecast_latlong(latlong: tuple[float, float] = default_location_coordinates, unit: str = default_units) -> dict:
	"""
	Fetches the 5-day weather forecast for a specified location.
	
	Args:
		latlong (tuple): (lat, long) of the location to fetch forecast for
		unit (str): Temperature unit, 'C' for Celsius or 'F' for Fahrenheit
	
	Returns:
		dict: Weather forecast data including daily temperatures, descriptions, and humidity
	"""
	FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
	
	# Convert unit parameter to API format
	units = 'imperial' if unit.upper() == 'F' else 'metric'
	
	params = {
		'lat': latlong[0],
		'lon': latlong[1],
		'appid': WEATHER_API_KEY,
		'units': units
	}
	
	try:
		response = requests.get(FORECAST_URL, params=params)
		response.raise_for_status()
		return response.json()
		
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 401:
			raise Exception("Invalid API key. Please check your OpenWeatherMap API key in the .env file")
		elif e.response.status_code == 404:
			raise Exception(f"Latlong {latlong} not found")
		else:
			raise Exception(f"HTTP error occurred: {str(e)}")
	except requests.exceptions.ConnectionError:
		raise Exception("Failed to connect to weather service. Please check your internet connection")
	except requests.exceptions.Timeout:
		raise Exception("Request timed out. Please try again")
	except requests.exceptions.RequestException as e:
		raise Exception(f"An error occurred while fetching forecast data: {str(e)}")
	except KeyError as e:
		raise Exception(f"Unexpected response format from weather service: {str(e)}")

def get_5_day_weather_forecast_city(location: str, unit: str = default_units) -> dict:
	"""
	Fetches the 5-day weather forecast for a specified location by city name

	Args:
		location (str): City name (e.g., "London", "New York, US", "San Francisco, CA, US")
			Note: If you supply a state, you must also supply the country code; 
			otherwise, the API will think you're calling the state as a country
		unit (str): Temperature unit, 'C' for Celsius or 'F' for Fahrenheit
	
	Returns:
		dict: Weather forecast data including temperature, description, and humidity
	"""
	latlong = get_location_coordinates(location)
	return get_5_day_weather_forecast_latlong(latlong, unit)

def test_get_location_coordinates():
	"""
	Tests the get_location_coordinates function
	"""
	location = get_location_coordinates('San Francisco')
	expected_coordinates = (37.7790262, -122.419906)
	return location == expected_coordinates

def test_get_current_weather_city():
	"""
	Tests the get_current_weather_city function
	"""
	print(get_current_weather_city('San Francisco, CA, US'))

def test_get_current_weather_latlong():
	"""
	Tests the get_current_weather_latlong function
	"""
	print(get_current_weather_latlong())

def test_get_hourly_weather_forecast_latlong():
	"""
	Tests the get_hourly_weather_forecast_latlong function
	"""
	print(get_hourly_weather_forecast_latlong())

def test_get_hourly_weather_forecast_city():
	"""
	Tests the get_hourly_weather_forecast_city function
	"""
	print(get_hourly_weather_forecast_city('San Francisco, CA, US'))

def test_get_5_day_weather_forecast_latlong():
	"""
	Tests the get_5_day_weather_forecast_latlong function
	"""
	print(get_5_day_weather_forecast_latlong())

def test_get_5_day_weather_forecast_city():
	"""
	Tests the get_5_day_weather_forecast_city function
	"""
	print(get_5_day_weather_forecast_city('Chicago, IL, US'))