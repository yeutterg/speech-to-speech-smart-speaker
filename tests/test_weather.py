import pytest
import requests
from unittest.mock import Mock, patch
from tools.weather import WeatherTool

@pytest.fixture
def api_key():
    """Test API key"""
    return "test_api_key"

@pytest.fixture
def weather_tool(api_key):
    """Create WeatherTool instance for testing"""
    return WeatherTool(api_key=api_key)

@pytest.fixture
def mock_weather_response():
    """Mock weather API response"""
    return {
        "coord": {"lon": -122.4194, "lat": 37.7749},
        "weather": [
            {
                "id": 800,
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d"
            }
        ],
        "main": {
            "temp": 72.5,
            "feels_like": 71.8,
            "temp_min": 65.3,
            "temp_max": 77.2,
            "pressure": 1012,
            "humidity": 64
        },
        "wind": {
            "speed": 8.05,
            "deg": 300
        },
        "name": "San Francisco"
    }

@pytest.fixture
def mock_forecast_response():
    """Mock forecast API response"""
    return {
        "hourly": [
            {
                "dt": 1618317040,
                "temp": 72.5,
                "feels_like": 71.8,
                "pressure": 1012,
                "humidity": 64,
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def mock_geocoding_response():
    """Mock geocoding API response"""
    return [
        {
            "name": "San Francisco",
            "lat": 37.7749,
            "lon": -122.4194,
            "country": "US",
            "state": "California"
        }
    ]

class TestWeatherTool:
    """Test suite for WeatherTool class"""

    def test_initialization(self, weather_tool):
        """Test WeatherTool initialization"""
        assert isinstance(weather_tool, WeatherTool)
        assert weather_tool.api_key == "test_api_key"
        assert weather_tool.default_location == (37.7749, -122.4194)

    def test_name_property(self, weather_tool):
        """Test name property returns correct value"""
        assert weather_tool.name == "get_weather"

    def test_description_property(self, weather_tool):
        """Test description property returns non-empty string"""
        assert isinstance(weather_tool.description, str)
        assert len(weather_tool.description) > 0

    def test_parameters_property(self, weather_tool):
        """Test parameters property returns valid schema"""
        params = weather_tool.parameters
        assert isinstance(params, dict)
        assert "type" in params
        assert "properties" in params

    @patch('requests.get')
    def test_get_location_coordinates(self, mock_get, weather_tool, mock_geocoding_response):
        """Test getting coordinates from city name"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_geocoding_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test successful case
        coordinates = weather_tool._get_location_coordinates("San Francisco")
        assert coordinates == (37.7749, -122.4194)

        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "geo/1.0/direct" in args[0]
        assert kwargs['params']['q'] == "San Francisco"

    @patch('requests.get')
    def test_get_current_weather(self, mock_get, weather_tool, mock_weather_response):
        """Test getting current weather"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test with coordinates
        result = weather_tool.get_current_weather((37.7749, -122.4194), "F")
        assert result == mock_weather_response

        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "weather" in args[0]
        assert kwargs['params']['lat'] == 37.7749
        assert kwargs['params']['lon'] == -122.4194

    @patch('requests.get')
    def test_get_hourly_forecast(self, mock_get, weather_tool, mock_forecast_response):
        """Test getting hourly forecast"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_forecast_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test with coordinates
        result = weather_tool.get_hourly_forecast((37.7749, -122.4194), "F")
        assert result == mock_forecast_response

    @patch('requests.get')
    def test_get_current_weather_by_city(self, mock_get, weather_tool, mock_geocoding_response, mock_weather_response):
        """Test getting current weather using city name"""
        # Setup mock responses for both API calls
        mock_responses = [
            Mock(json=lambda: mock_geocoding_response),
            Mock(json=lambda: mock_weather_response)
        ]
        for response in mock_responses:
            response.raise_for_status.return_value = None
        mock_get.side_effect = mock_responses

        # Test with city name
        result = weather_tool.get_current_weather_by_city("San Francisco", "F")
        assert result == mock_weather_response

        # Verify both API calls were made
        assert mock_get.call_count == 2

    def test_execute_invalid_forecast_type(self, weather_tool):
        """Test execute method with invalid forecast type"""
        with pytest.raises(ValueError):
            weather_tool.execute(forecast_type="invalid")

    @patch('requests.get')
    def test_api_error_handling(self, mock_get, weather_tool):
        """Test handling of API errors"""
        # Test unauthorized error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=Mock(status_code=401)
        )
        mock_get.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            weather_tool.get_current_weather((37.7749, -122.4194), "F")
        assert "Invalid API key" in str(exc_info.value)

        # Test connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(Exception) as exc_info:
            weather_tool.get_current_weather((37.7749, -122.4194), "F")
        assert "Failed to connect" in str(exc_info.value)

    @patch('requests.get')
    def test_execute_method(self, mock_get, weather_tool, mock_weather_response):
        """Test the main execute method"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test with default parameters
        result = weather_tool.execute(forecast_type="current")
        assert result == mock_weather_response

        # Test with custom parameters
        result = weather_tool.execute(
            forecast_type="current",
            unit="C"
        )
        assert result == mock_weather_response
