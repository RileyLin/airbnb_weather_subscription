# Weather Alert Service for Property Owners

This service provides automated weather alerts and maintenance recommendations for property owners, specifically tailored for properties at different elevations and with varying yard sizes.

## Features

- Daily weather updates (sent at 8:00 AM)
- Weekly weather summaries (sent on Sundays at 9:00 AM)
- Custom recommendations based on:
  - Property elevation
  - Yard size
  - Current season
  - Weather conditions

## Setup

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure email settings:
   - The service uses Gmail for sending emails
   - You need to generate an App Password for your Gmail account:
     1. Go to your Google Account settings
     2. Navigate to Security
     3. Enable 2-Step Verification if not already enabled
     4. Go to App Passwords
     5. Generate a new app password for "Mail"
     6. Copy the generated password

3. Update the `.env` file with your credentials:
   ```
   OPENWEATHER_API_KEY=your_api_key
   SENDER_EMAIL=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

## Usage

1. To add a new subscriber:
   ```bash
   python add_subscriber.py
   ```
   Follow the prompts to enter the subscriber's information.

2. To start the weather service:
   ```bash
   python weather_service.py
   ```
   The service will run continuously, sending updates at scheduled times.

## Weather Alerts Include

- Temperature warnings (freezing conditions, high heat)
- Precipitation alerts (rain, snow)
- Seasonal maintenance reminders
- Elevation-specific precautions
- Property maintenance recommendations

## Requirements

- Python 3.7 or higher
- Internet connection
- Gmail account
- OpenWeatherMap API key 