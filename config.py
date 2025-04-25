import os
from datetime import datetime, timedelta

# Bot configuration
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")  # Get token from environment variable

# Admin configuration
ADMIN_IDS = [1006518993]  # List of admin user IDs
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")  # Password for admin authentication

# Booking configuration
BOOKING_START_HOUR = 9  # Earliest booking time (9:00 AM)
BOOKING_END_HOUR = 21   # Latest booking time (9:00 PM)
DAYS_IN_ADVANCE = 7     # How many days in advance bookings are allowed

# Time slots available for booking (1-hour increments)
def get_available_time_slots():
    return [f"{hour:02d}:00-{(hour+1):02d}:00" for hour in range(BOOKING_START_HOUR, BOOKING_END_HOUR)]

# Get date range for the next DAYS_IN_ADVANCE days
def get_date_range():
    today = datetime.now().date()
    return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(DAYS_IN_ADVANCE)]
