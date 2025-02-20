import os
from weather_service import WeatherService
from dotenv import load_dotenv

def test_weather_service():
    # Load environment variables
    load_dotenv()
    
    # Create weather service instance
    service = WeatherService()
    
    # Test locations
    test_locations = [
        "98812",  # Brewster, WA zip code
        "10001",  # New York zip code
        "90210",  # Beverly Hills zip code
    ]
    
    for location in test_locations:
        try:
            print(f"\nTesting location: {location}")
            
            # Test coordinate lookup
            print("1. Testing coordinate lookup...")
            coords = service._get_coordinates(location)
            print(f"✓ Coordinates found: {coords}")
            
            # Test weather forecast
            print("2. Testing weather forecast...")
            forecast = service.get_weather_forecast(coords['lat'], coords['lon'])
            print(f"✓ Forecast received with {len(forecast['daily'])} days of data")
            
            # Test weather analysis
            print("3. Testing weather analysis...")
            tomorrow = forecast['daily'][1]
            precautions = service.analyze_weather_conditions(tomorrow, 1000)  # Using 1000ft elevation for testing
            print("✓ Weather analysis complete")
            print("Precautions:", precautions)
            
            print(f"\n✅ All tests passed for location: {location}\n")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error testing location {location}: {str(e)}")
            print("-" * 50)

if __name__ == "__main__":
    test_weather_service() 