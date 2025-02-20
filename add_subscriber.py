from weather_service import WeatherService

def add_new_subscriber():
    print("Welcome to the Weather Alert Service!")
    print("Please provide the following information:")
    
    email = input("Email address: ")
    location = input("Location (city, state): ")
    yard_size = float(input("Yard size (in acres): "))
    elevation = float(input("Elevation (in feet): "))
    
    service = WeatherService()
    
    try:
        service.add_subscriber(email, location, yard_size, elevation)
        print("\nSubscription successful! You will receive:")
        print("1. Daily weather updates at 8:00 AM")
        print("2. Weekly weather summaries on Sundays at 9:00 AM")
    except Exception as e:
        print(f"\nError adding subscriber: {str(e)}")

if __name__ == "__main__":
    add_new_subscriber() 