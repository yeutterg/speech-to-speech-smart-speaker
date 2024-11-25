import requests
from typing import Dict, Any, Tuple, Optional
from tools import BaseTool

class WeatherTool(BaseTool):
    """Tool for fetching weather information from OpenWeatherMap API"""

    def __init__(self, api_key: str, default_location: Tuple[float, float] = (37.7749, -122.4194), default_units: str = 'F'):
        """
        Initialize WeatherTool.
        
        Args:
            api_key (str): OpenWeatherMap API key
            default_location (Tuple[float, float]): Default (lat, long) to use when no location specified
            default_units (str): Default temperature unit ('F', 'C', or 'K')
        """
        self.api_key = api_key
        self.default_location = default_location
        self.default_units = default_units

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get weather information for a location. Provide forecast_type ('current', 'hourly', or '5day') and optionally a location name and unit ('F', 'C', or 'K')."

    def execute(self, forecast_type: str, location: str = None, unit: str = None) -> Dict[str, Any]:
        """Get weather information for a location.
        
        Args:
            forecast_type (str): Type of forecast ('current', 'hourly', or '5day')
            location (str, optional): City name (e.g., 'London', 'New York')
            unit (str, optional): Temperature unit ('F', 'C', or 'K')
            
        Returns:
            Dict[str, Any]: Weather information including temperature, humidity, and description
        """
        try:
            unit = unit or self.default_units
            
            if location:
                if forecast_type == "current":
                    result = self.get_current_weather_by_city(location, unit)
                elif forecast_type == "hourly":
                    result = self.get_hourly_forecast_by_city(location, unit)
                elif forecast_type == "5day":
                    result = self.get_5day_forecast_by_city(location, unit)
                else:
                    raise ValueError(f"Invalid forecast type: {forecast_type}")
            else:
                if forecast_type == "current":
                    result = self.get_current_weather(self.default_location, unit)
                elif forecast_type == "hourly":
                    result = self.get_hourly_forecast(self.default_location, unit)
                elif forecast_type == "5day":
                    result = self.get_5day_forecast(self.default_location, unit)
                else:
                    raise ValueError(f"Invalid forecast type: {forecast_type}")
            
            return self.format_weather_response(result, forecast_type)
                    
        except Exception as e:
            return {"error": str(e)}

    def _get_location_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a location using OpenWeather's geocoding API."""
        GEOCODING_URL = 'http://api.openweathermap.org/geo/1.0/direct'
        
        params = {
            'q': location,
            'limit': 1,
            'appid': self.api_key
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

    def get_current_weather(self, latlong: Tuple[float, float], unit: str = None) -> Dict[str, Any]:
        """Get current weather conditions using coordinates."""
        unit = unit or self.default_units
        BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
        
        units = 'imperial' if unit.upper() == 'F' else 'metric'
        
        params = {
            'lat': latlong[0],
            'lon': latlong[1],
            'appid': self.api_key,
            'units': units
        }
        
        return self._make_request(BASE_URL, params)

    def get_current_weather_by_city(self, city: str, unit: str = None) -> Dict[str, Any]:
        """Get current weather conditions using city name."""
        unit = unit or self.default_units
        coordinates = self._get_location_coordinates(city)
        if not coordinates:
            raise ValueError(f"Could not find coordinates for city: {city}")
        return self.get_current_weather(coordinates, unit)

    def get_hourly_forecast(self, latlong: Tuple[float, float], unit: str = None) -> Dict[str, Any]:
        """Get hourly forecast using coordinates."""
        unit = unit or self.default_units
        FORECAST_URL = 'https://api.openweathermap.org/data/3.0/onecall'
        
        units = 'imperial' if unit.upper() == 'F' else 'metric'
        
        params = {
            'lat': latlong[0],
            'lon': latlong[1],
            'appid': self.api_key,
            'units': units,
            'exclude': 'current,minutely,daily,alerts'
        }
        
        return self._make_request(FORECAST_URL, params)

    def get_hourly_forecast_by_city(self, city: str, unit: str = None) -> Dict[str, Any]:
        """Get hourly forecast using city name."""
        unit = unit or self.default_units
        coordinates = self._get_location_coordinates(city)
        if not coordinates:
            raise ValueError(f"Could not find coordinates for city: {city}")
        return self.get_hourly_forecast(coordinates, unit)

    def get_5day_forecast(self, latlong: Tuple[float, float], unit: str = None) -> Dict[str, Any]:
        """Get 5-day forecast using coordinates."""
        unit = unit or self.default_units
        FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
        
        units = 'imperial' if unit.upper() == 'F' else 'metric'
        
        params = {
            'lat': latlong[0],
            'lon': latlong[1],
            'appid': self.api_key,
            'units': units
        }
        
        return self._make_request(FORECAST_URL, params)

    def get_5day_forecast_by_city(self, city: str, unit: str = None) -> Dict[str, Any]:
        """Get 5-day forecast using city name."""
        unit = unit or self.default_units
        coordinates = self._get_location_coordinates(city)
        if not coordinates:
            raise ValueError(f"Could not find coordinates for city: {city}")
        return self.get_5day_forecast(coordinates, unit)

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with error handling."""
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid API key. Please check your OpenWeatherMap API key")
            elif e.response.status_code == 404:
                raise Exception(f"Location not found")
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

    def format_weather_response(self, data: Dict[str, Any], forecast_type: str) -> Dict[str, Any]:
        """Format weather data into a user-friendly structure."""
        try:
            if forecast_type == "current":
                return {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "location": data.get("name", "Unknown"),
                    "unit": self.default_units
                }
            elif forecast_type == "hourly":
                return {
                    "hourly_forecast": [
                        {
                            "time": hour["dt"],
                            "temperature": hour["temp"],
                            "description": hour["weather"][0]["description"],
                            "humidity": hour["humidity"]
                        } for hour in data.get("hourly", [])[:24]  # First 24 hours
                    ],
                    "unit": self.default_units
                }
            elif forecast_type == "5day":
                return {
                    "daily_forecast": [
                        {
                            "time": item["dt"],
                            "temperature": item["main"]["temp"],
                            "description": item["weather"][0]["description"],
                            "humidity": item["main"]["humidity"]
                        } for item in data.get("list", [])
                    ],
                    "unit": self.default_units
                }
            return data
        except KeyError as e:
            raise Exception(f"Error formatting weather data: {str(e)}")
