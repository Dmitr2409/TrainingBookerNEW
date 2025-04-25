import re
from datetime import datetime

def validate_phone_number(phone):
    """
    Validate if the provided string is a valid phone number.
    Allows formats like: +1234567890, 1234567890, 123-456-7890
    """
    # Remove any non-digit characters except for the leading plus sign
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # Check if the phone number is valid (starts with optional + and has 10-15 digits)
    if re.match(r'^\+?\d{10,15}$', phone_clean):
        return True
    return False

def validate_name(name):
    """
    Validate if the provided string is a valid name.
    Name should be 2-50 characters and contain only letters, spaces, and hyphens.
    """
    if re.match(r'^[A-Za-zА-Яа-яЁёІіЇїЄє\s\-]{2,50}$', name):
        return True
    return False

def format_date_for_display(date_str):
    """
    Convert date from YYYY-MM-DD to DD.MM.YYYY format
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d.%m.%Y')
    except ValueError:
        return date_str

def format_booking_info(booking):
    """
    Format booking information for display to users
    """
    date_display = format_date_for_display(booking['date'])
    
    return (
        f"📅 Дата: {date_display}\n"
        f"⏰ Время: {booking['time']}\n"
        f"👤 Имя: {booking['name']}\n"
        f"📞 Телефон: {booking['phone']}\n"
        f"🕒 Создано: {booking['created_at']}"
    )
