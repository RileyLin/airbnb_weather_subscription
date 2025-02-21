import os
import json
import requests
import schedule
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List
import pytz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
    def get_weather_forecast(self, lat: float, lon: float) -> Dict:
        """Get 7-day weather forecast for given coordinates."""
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=imperial&appid={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            logger.info(f"API Response for coordinates ({lat}, {lon}): {data}")
            
            if 'daily' not in data:
                logger.error(f"No daily data in API response: {data}")
                if 'message' in data:
                    raise ValueError(f"API Error: {data['message']}")
                raise ValueError("No daily forecast data in API response")
                
            return data
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise ValueError(f"Failed to fetch weather data: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            raise ValueError("Invalid response from weather API")
        
    def analyze_weather_conditions(self, forecast: Dict, elevation: float) -> List[str]:
        """Analyze weather conditions and return necessary precautions."""
        precautions = []
        
        # Analyze temperature
        temp = forecast['temp']['day']
        if temp < 32:
            precautions.append("❄️ Freezing temperatures expected. Protect water pipes and ensure heating system is working.")
        elif temp > 85:
            precautions.append("🌡️ High temperatures expected. Ensure AC is functioning properly.")
            
        # Analyze precipitation
        if forecast.get('snow', 0) > 0:
            precautions.append("🌨️ Snowfall expected. Clear walkways and check snow removal equipment.")
            
        if forecast.get('rain', 0) > 0.5:
            precautions.append("🌧️ Heavy rain expected. Check gutters and drainage systems.")
            
        # Spring/Summer specific (March through August)
        current_month = datetime.now().month
        if 3 <= current_month <= 8:
            precautions.append("🌱 Regular yard maintenance may be needed - check for weed growth.")
            
        # Elevation specific
        if elevation > 2000:
            precautions.append("⛰️ High elevation location - monitor road conditions and access routes.")
            
        return precautions
        
    def send_email(self, to_email: str, subject: str, content: str):
        """Send email to subscriber using Gmail SMTP."""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'html'))
        
        try:
            logger.info(f"Attempting to establish SMTP connection to Gmail server")
            import ssl
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                logger.info(f"SMTP connection established. Attempting login with sender email: {self.sender_email}")
                server.login(self.sender_email, self.email_password)
                logger.info("SMTP login successful")
                
                logger.info(f"Attempting to send email to: {to_email}")
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {str(e)}")
            raise ValueError("Failed to authenticate with Gmail. Please check your email and password.")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise ValueError(f"Failed to send email: {str(e)}")

    def _get_coordinates(self, location: str) -> Dict[str, float]:
        """Get coordinates for a location using OpenWeatherMap API.
        If a 5-digit zip code is provided, use the zip code endpoint; otherwise use the direct search endpoint."""
        location = location.strip()
        try:
            if location.isdigit() and len(location) == 5:
                # Use zip code endpoint; defaulting country to US
                url = f"http://api.openweathermap.org/geo/1.0/zip?zip={location},US&appid={self.api_key}"
            else:
                url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.api_key}"
            
            logger.info(f"Fetching coordinates for location: {location}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Geocoding API response: {data}")
            
            if not data:
                raise ValueError(f"Could not find coordinates for location: {location}")
                
            if isinstance(data, dict):
                # Zip code endpoint returns a dict
                if 'lat' not in data or 'lon' not in data:
                    raise ValueError(f"Invalid coordinate data received for zip code {location}")
                coords = {'lat': data.get('lat'), 'lon': data.get('lon')}
            else:
                if not data or 'lat' not in data[0] or 'lon' not in data[0]:
                    raise ValueError(f"Invalid coordinate data received for location {location}")
                coords = {'lat': data[0]['lat'], 'lon': data[0]['lon']}
            
            logger.info(f"Coordinates found for {location}: {coords}")
            return coords
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch coordinates: {str(e)}")
            raise ValueError(f"Failed to fetch coordinates: {str(e)}")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse coordinate data: {str(e)}")
            raise ValueError(f"Failed to parse coordinate data: {str(e)}")

    def send_daily_update_for_subscriber(self, subscriber):
        """Send daily weather update for a specific subscriber."""
        forecast = self.get_weather_forecast(subscriber.latitude, subscriber.longitude)
        if 'daily' not in forecast or not forecast['daily']:
            raise Exception("No daily forecast data available from the API.")
        try:
            tomorrow = forecast['daily'][1]
        except IndexError:
            raise Exception("Daily forecast data is incomplete. Expected at least 2 days of forecast.")
        precautions = self.analyze_weather_conditions(tomorrow, subscriber.elevation)
        
        content = f"""
        <h2>Weather Update for {subscriber.location}</h2>
        <h3>Tomorrow's Forecast:</h3>
        <p>Temperature: {tomorrow['temp']['day']}°F</p>
        <p>Weather: {tomorrow['weather'][0]['description']}</p>
        <p>Precipitation Chance: {tomorrow['pop'] * 100}%</p>
        
        <h3>Recommended Precautions:</h3>
        <ul>
        {''.join([f'<li>{p}</li>' for p in precautions])}
        </ul>
        """
        
        self.send_email(
            subscriber.email,
            f"Daily Weather Update for {subscriber.location}",
            content
        )

    def send_weekly_summary_for_subscriber(self, subscriber):
        """Send weekly weather summary for a specific subscriber."""
        forecast = self.get_weather_forecast(subscriber.latitude, subscriber.longitude)
        if 'daily' not in forecast or not forecast['daily']:
            raise Exception("No daily forecast data available from the API.")
        content = "<h2>Weekly Weather Summary</h2>"
        for day in forecast['daily'][:7]:
            date = datetime.fromtimestamp(day['dt']).strftime('%A, %B %d')
            precautions = self.analyze_weather_conditions(day, subscriber.elevation)
            content += f"""
            <h3>{date}</h3>
            <p>Temperature: {day['temp']['day']}°F</p>
            <p>Weather: {day['weather'][0]['description']}</p>
            <p>Precipitation Chance: {day['pop'] * 100}%</p>
            
            <h4>Recommended Precautions:</h4>
            <ul>
            {''.join([f'<li>{p}</li>' for p in precautions])}
            </ul>
            <hr>
            """
        self.send_email(
            subscriber.email,
            f"Weekly Weather Summary for {subscriber.location}",
            content
        )

    def send_daily_update(self):
        """Send daily updates to all active subscribers."""
        from models import Subscriber, db
        with db.session.begin():
            subscribers = Subscriber.query.filter_by(active=True).all()
            for subscriber in subscribers:
                try:
                    self.send_daily_update_for_subscriber(subscriber)
                except Exception as e:
                    logger.error(f"Failed to send daily update to {subscriber.email}: {str(e)}")

    def send_weekly_summary(self):
        """Send weekly summary to all active subscribers."""
        from models import Subscriber, db
        with db.session.begin():
            subscribers = Subscriber.query.filter_by(active=True).all()
            for subscriber in subscribers:
                try:
                    self.send_weekly_summary_for_subscriber(subscriber)
                except Exception as e:
                    logger.error(f"Failed to send weekly summary to {subscriber.email}: {str(e)}")

def main():
    service = WeatherService()
    
    # Schedule daily updates (8 AM local time)
    schedule.every().day.at("08:00").do(service.send_daily_update)
    
    # Schedule weekly summary (Sunday at 9 AM local time)
    schedule.every().sunday.at("09:00").do(service.send_weekly_summary)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 