from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    """Create the main menu keyboard with the primary options"""
    keyboard = [
        [KeyboardButton('📅 Забронировать')],
        [KeyboardButton('🔍 Мои бронирования')],
        [KeyboardButton('📋 Все бронирования')],
        [KeyboardButton('⏰ Свободное время')],
        [KeyboardButton('👤 Админ панель')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def generate_dates_keyboard(dates):
    """Generate a keyboard with available dates"""
    keyboard = []
    for date_str in dates:
        # Format the date for display (YYYY-MM-DD to DD.MM.YYYY)
        display_date = date_str.split('-')
        display_date = f"{display_date[2]}.{display_date[1]}.{display_date[0]}"
        keyboard.append([InlineKeyboardButton(display_date, callback_data=f"date_{date_str}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def generate_times_keyboard(times):
    """Generate a keyboard with available times"""
    keyboard = []
    row = []
    
    for i, time in enumerate(times):
        row.append(InlineKeyboardButton(time, callback_data=f"time_{time}"))
        
        # Create rows with 3 buttons each
        if (i + 1) % 3 == 0 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(keyboard)

def generate_bookings_keyboard(bookings):
    """Generate a keyboard to display user's bookings with cancel options"""
    keyboard = []
    
    for booking in bookings:
        date_parts = booking['date'].split('-')
        display_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        button_text = f"{display_date} {booking['time']} - {booking['name']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_{booking['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def booking_actions_keyboard(booking_id):
    """Generate a keyboard with actions for a specific booking"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить бронирование", callback_data=f"cancel_{booking_id}")],
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_bookings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu_keyboard():
    """Generate the admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📋 Все бронирования", callback_data="admin_all_bookings")],
        [InlineKeyboardButton("❌ Сбросить все бронирования", callback_data="admin_reset_all")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_bookings_keyboard(bookings):
    """Generate a keyboard to display all bookings with cancel options for admin"""
    keyboard = []
    
    for booking in bookings:
        date_parts = booking['date'].split('-')
        display_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        button_text = f"{display_date} {booking['time']} - {booking['name']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_view_{booking['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")])
    return InlineKeyboardMarkup(keyboard)

def admin_booking_actions_keyboard(booking_id):
    """Generate a keyboard with admin actions for a specific booking"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить бронирование", callback_data=f"admin_cancel_{booking_id}")],
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_admin_bookings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard():
    """Generate a keyboard with just a cancel button"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_operation")]]
    return InlineKeyboardMarkup(keyboard)

def admin_confirm_reset_keyboard():
    """Generate a confirmation keyboard for resetting all bookings"""
    keyboard = [
        [InlineKeyboardButton("✅ Да, сбросить все", callback_data="confirm_reset_all")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)
