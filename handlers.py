import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler

import config
from data_store import store
from keyboard_markups import (
    main_menu_keyboard, generate_dates_keyboard, generate_times_keyboard,
    generate_bookings_keyboard, booking_actions_keyboard, admin_menu_keyboard,
    admin_bookings_keyboard, admin_booking_actions_keyboard, cancel_keyboard,
    admin_confirm_reset_keyboard
)
from utils import validate_phone_number, validate_name, format_booking_info

# Define states for conversation handlers
(
    SELECTING_DATE, SELECTING_TIME, ENTERING_NAME, ENTERING_PHONE,
    CONFIRMING_BOOKING, VIEWING_BOOKINGS, ADMIN_AUTH, ADMIN_MENU,
    VIEWING_ADMIN_BOOKINGS, ADMIN_CONFIRMING_RESET
) = range(10)

# Command handlers
def start_command(update: Update, context: CallbackContext):
    """Handler for the /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    welcome_message = (
        f"👋 Привет, {user_name}!\n\n"
        "Это бот для бронирования места для тренировок.\n"
        "Выберите опцию из меню ниже:"
    )
    
    # Clear any existing user state
    store.clear_user_state(user_id)
    
    update.message.reply_text(
        welcome_message,
        reply_markup=main_menu_keyboard()
    )
    
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext):
    """Handler for the /help command"""
    help_text = (
        "🔍 *Как пользоваться ботом:*\n\n"
        "*📅 Забронировать* - создать новое бронирование, выбрав дату и время\n"
        "*🔍 Мои бронирования* - просмотр и отмена ваших бронирований\n"
        "*⏰ Свободное время* - проверка доступных слотов на ближайшие дни\n"
        "*👤 Админ панель* - панель управления для администраторов\n\n"
        "Если у вас возникли вопросы, пожалуйста, свяжитесь с администратором."
    )
    
    update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

# Booking flow handlers
def start_booking(update: Update, context: CallbackContext):
    """Start the booking process by showing available dates"""
    user_id = update.effective_user.id
    
    # Initialize new booking state with required fields
    initial_data = {
        'user_id': user_id,
        'state': 'booking'
    }
    
    # Set initial state
    store.set_user_state(user_id, 'booking', initial_data)
    
    # Get available dates for booking
    dates = config.get_date_range()
    
    update.message.reply_text(
        "📅 Выберите дату для бронирования:",
        reply_markup=generate_dates_keyboard(dates)
    )
    
    return SELECTING_DATE

def date_selected(update: Update, context: CallbackContext):
    """Handle date selection and show available times"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    selected_date = query.data.split('_')[1]  # Extract date from callback
    
    # Update user state with selected date
    user_state = store.get_user_state(user_id)
    if 'data' not in user_state:
        user_state['data'] = {}
    user_state['data']['selected_date'] = selected_date
    store.set_user_state(user_id, 'booking', user_state['data'])
    
    # Get available time slots for the selected date
    all_time_slots = config.get_available_time_slots()
    available_slots = store.get_available_slots(selected_date, all_time_slots)
    
    if not available_slots:
        query.edit_message_text(
            f"На выбранную дату нет свободных слотов. Пожалуйста, выберите другую дату.",
            reply_markup=generate_dates_keyboard(config.get_date_range())
        )
        return SELECTING_DATE
    
    # Format the date for display (YYYY-MM-DD to DD.MM.YYYY)
    display_date = selected_date.split('-')
    display_date = f"{display_date[2]}.{display_date[1]}.{display_date[0]}"
    
    query.edit_message_text(
        f"Дата: {display_date}\n\nВыберите время:",
        reply_markup=generate_times_keyboard(available_slots)
    )
    
    return SELECTING_TIME

def time_selected(update: Update, context: CallbackContext):
    """Handle time selection and ask for user's name"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    selected_time = query.data.split('_')[1]  # Extract time from callback
    
    # Get or initialize user state
    user_state = store.get_user_state(user_id)
    if 'data' not in user_state:
        user_state['data'] = {}
    
    # Update user state with selected time
    user_state['data']['selected_time'] = selected_time
    store.set_user_state(user_id, 'booking', user_state['data'])
    
    query.edit_message_text(
        "Введите ваше имя:",
        reply_markup=cancel_keyboard()
    )
    
    return ENTERING_NAME

def name_entered(update: Update, context: CallbackContext):
    """Handle name input and ask for phone number"""
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    # Validate name
    if not validate_name(name):
        update.message.reply_text(
            "Пожалуйста, введите корректное имя (только буквы, пробелы и дефисы, 2-50 символов):",
            reply_markup=cancel_keyboard()
        )
        return ENTERING_NAME
    
    # Get or initialize user state
    user_state = store.get_user_state(user_id)
    if 'data' not in user_state:
        user_state['data'] = {}
    
    # Update user state with entered name
    user_state['data']['name'] = name
    store.set_user_state(user_id, 'booking', user_state['data'])
    
    update.message.reply_text(
        "Введите ваш номер телефона:",
        reply_markup=cancel_keyboard()
    )
    
    return ENTERING_PHONE

def phone_entered(update: Update, context: CallbackContext):
    """Handle phone number input and confirm booking"""
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    # Get current user state
    user_state = store.get_user_state(user_id)
    if not user_state or 'data' not in user_state:
        update.message.reply_text(
            "Произошла ошибка с сохранением данных. Пожалуйста, начните бронирование заново, нажав кнопку '📅 Забронировать'",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
        
    # Validate phone number
    if not validate_phone_number(phone):
        update.message.reply_text(
            "Пожалуйста, введите корректный номер телефона:",
            reply_markup=cancel_keyboard()
        )
        return ENTERING_PHONE
    
    # Get or initialize user state
    user_state = store.get_user_state(user_id)
    if 'data' not in user_state:
        update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните бронирование заново.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Update user state with entered phone
    user_state['data']['phone'] = phone
    store.set_user_state(user_id, 'booking', user_state['data'])
    
    # Check if we have all required data
    required_fields = ['selected_date', 'selected_time', 'name']
    if not all(field in user_state['data'] for field in required_fields):
        update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните бронирование заново.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Get booking details for confirmation
    booking_data = user_state['data']
    date_parts = booking_data['selected_date'].split('-')
    display_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
    
    confirmation_text = (
        "Пожалуйста, проверьте детали бронирования:\n\n"
        f"📅 Дата: {display_date}\n"
        f"⏰ Время: {booking_data['selected_time']}\n"
        f"👤 Имя: {booking_data['name']}\n"
        f"📞 Телефон: {booking_data['phone']}\n\n"
        "Всё верно?"
    )
    
    # Create confirmation keyboard
    keyboard = [
        [{"text": "✅ Подтвердить", "callback_data": "confirm_booking"}],
        [{"text": "❌ Отмена", "callback_data": "cancel_operation"}]
    ]
    
    update.message.reply_text(
        confirmation_text,
        reply_markup={"inline_keyboard": keyboard}
    )
    
    return CONFIRMING_BOOKING

def confirm_booking(update: Update, context: CallbackContext):
    """Handle booking confirmation and save booking"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    user_state = store.get_user_state(user_id)
    booking_data = user_state['data']
    
    # Check if the time slot is still available
    if not store.is_time_slot_available(booking_data['selected_date'], booking_data['selected_time']):
        query.edit_message_text(
            "К сожалению, это время уже забронировано. Пожалуйста, выберите другое время.",
            reply_markup=None
        )
        
        # Restart the booking process
        dates = config.get_date_range()
        query.message.reply_text(
            "📅 Выберите дату для бронирования:",
            reply_markup=generate_dates_keyboard(dates)
        )
        return SELECTING_DATE
    
    # Save the booking
    booking_id = store.add_booking(
        user_id,
        booking_data['selected_date'],
        booking_data['selected_time'],
        booking_data['name'],
        booking_data['phone']
    )
    
    # Clear user state
    store.clear_user_state(user_id)
    
    query.edit_message_text(
        "✅ Бронирование успешно создано!\n\n"
        f"Номер бронирования: #{booking_id}\n\n"
        "Вы можете просмотреть или отменить бронирование в разделе 'Мои бронирования'.",
        reply_markup=None
    )
    
    return ConversationHandler.END

def view_available_times(update: Update, context: CallbackContext):
    """Show available time slots for the next several days"""
    dates = config.get_date_range()
    all_time_slots = config.get_available_time_slots()
    
    availability_text = "⏰ *Доступное время для бронирования:*\n\n"
    
    for date in dates:
        # Get available slots for this date
        available_slots = store.get_available_slots(date, all_time_slots)
        
        # Format the date for display
        date_parts = date.split('-')
        display_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        
        if available_slots:
            # Format the slots in groups of 3 for readability
            slot_groups = [available_slots[i:i+3] for i in range(0, len(available_slots), 3)]
            formatted_slots = '\n'.join([', '.join(group) for group in slot_groups])
            
            availability_text += f"📅 *{display_date}*:\n{formatted_slots}\n\n"
        else:
            availability_text += f"📅 *{display_date}*: Нет свободных слотов\n\n"
    
    update.message.reply_text(
        availability_text,
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

# My bookings handlers
def view_my_bookings(update: Update, context: CallbackContext):
    """Show user's bookings with options to cancel"""
    user_id = update.effective_user.id
    
    # Get all bookings for this user
    user_bookings = store.get_bookings_for_user(user_id)
    
    if not user_bookings:
        update.message.reply_text(
            "У вас нет активных бронирований.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    update.message.reply_text(
        "🔍 Ваши бронирования:\n"
        "Выберите бронирование для просмотра деталей.",
        reply_markup=generate_bookings_keyboard(user_bookings)
    )
    
    return VIEWING_BOOKINGS

def view_booking_details(update: Update, context: CallbackContext):
    """Show details for a specific booking"""
    query = update.callback_query
    query.answer()
    
    booking_id = int(query.data.split('_')[1])
    booking = store.bookings.get(booking_id)
    
    if not booking:
        query.edit_message_text(
            "Бронирование не найдено или было отменено.",
            reply_markup=generate_bookings_keyboard(
                store.get_bookings_for_user(update.effective_user.id)
            )
        )
        return VIEWING_BOOKINGS
    
    booking_info = format_booking_info(booking)
    
    query.edit_message_text(
        f"📋 *Детали бронирования #{booking_id}*\n\n{booking_info}",
        reply_markup=booking_actions_keyboard(booking_id),
        parse_mode='Markdown'
    )
    
    return VIEWING_BOOKINGS

def cancel_booking(update: Update, context: CallbackContext):
    """Cancel a specific booking"""
    query = update.callback_query
    query.answer()
    
    booking_id = int(query.data.split('_')[1])
    
    # Attempt to cancel the booking
    success = store.cancel_booking(booking_id)
    
    if success:
        query.edit_message_text(
            f"✅ Бронирование #{booking_id} успешно отменено.",
            reply_markup=None
        )
        
        # Show updated bookings list
        user_bookings = store.get_bookings_for_user(update.effective_user.id)
        
        if user_bookings:
            query.message.reply_text(
                "🔍 Ваши бронирования:",
                reply_markup=generate_bookings_keyboard(user_bookings)
            )
        else:
            query.message.reply_text(
                "У вас нет активных бронирований.",
                reply_markup=main_menu_keyboard()
            )
            return ConversationHandler.END
    else:
        query.edit_message_text(
            "❌ Не удалось отменить бронирование. Возможно, оно уже было отменено.",
            reply_markup=None
        )
        
        # Return to main menu
        query.message.reply_text(
            "Возвращение в главное меню.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    return VIEWING_BOOKINGS

# Admin panel handlers
def admin_panel(update: Update, context: CallbackContext):
    """Access the admin panel"""
    user_id = update.effective_user.id
    
    # Check if user is in the admin list
    if user_id in config.ADMIN_IDS:
        # Автоматично аутентифікуємо користувача з дозволеним ID
        store.authenticate_admin(user_id)
        update.message.reply_text(
            "👑 *Панель администратора*\n\n"
            "Выберите действие:",
            reply_markup=admin_menu_keyboard(),
            parse_mode='Markdown'
        )
        return ADMIN_MENU
        
    # Check if already authenticated
    if store.is_admin_authenticated(user_id):
        update.message.reply_text(
            "👑 *Панель администратора*\n\n"
            "Выберите действие:",
            reply_markup=admin_menu_keyboard(),
            parse_mode='Markdown'
        )
        return ADMIN_MENU
    
    # Ask for password
    update.message.reply_text(
        "Пожалуйста, введите пароль администратора:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADMIN_AUTH

def admin_auth(update: Update, context: CallbackContext):
    """Authenticate admin with password"""
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    # Delete message with password for security
    update.message.delete()
    
    if password == config.ADMIN_PASSWORD:
        # Authenticate admin
        store.authenticate_admin(user_id)
        
        update.message.reply_text(
            "✅ Аутентификация успешна.\n\n"
            "👑 *Панель администратора*\n\n"
            "Выберите действие:",
            reply_markup=admin_menu_keyboard(),
            parse_mode='Markdown'
        )
        return ADMIN_MENU
    else:
        update.message.reply_text(
            "❌ Неверный пароль.\n\n"
            "Возвращение в главное меню.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

def admin_view_all_bookings(update: Update, context: CallbackContext):
    """Admin view of all bookings"""
    query = update.callback_query
    query.answer()
    
    all_bookings = store.get_all_bookings()
    
    if not all_bookings:
        query.edit_message_text(
            "В системе нет активных бронирований.",
            reply_markup=admin_menu_keyboard()
        )
        return ADMIN_MENU
    
    query.edit_message_text(
        "📋 *Все бронирования:*\n"
        "Выберите бронирование для просмотра деталей.",
        reply_markup=admin_bookings_keyboard(all_bookings),
        parse_mode='Markdown'
    )
    
    return VIEWING_ADMIN_BOOKINGS

def admin_view_booking_details(update: Update, context: CallbackContext):
    """Admin view of specific booking details"""
    query = update.callback_query
    query.answer()
    
    booking_id = int(query.data.split('_')[2])  # Extract ID from admin_view_X
    booking = store.bookings.get(booking_id)
    
    if not booking:
        query.edit_message_text(
            "Бронирование не найдено или было отменено.",
            reply_markup=admin_bookings_keyboard(store.get_all_bookings())
        )
        return VIEWING_ADMIN_BOOKINGS
    
    booking_info = format_booking_info(booking)
    
    query.edit_message_text(
        f"📋 *Детали бронирования #{booking_id}*\n\n{booking_info}",
        reply_markup=admin_booking_actions_keyboard(booking_id),
        parse_mode='Markdown'
    )
    
    return VIEWING_ADMIN_BOOKINGS

def admin_cancel_booking(update: Update, context: CallbackContext):
    """Admin cancellation of a booking"""
    query = update.callback_query
    query.answer()
    
    booking_id = int(query.data.split('_')[2])  # Extract ID from admin_cancel_X
    
    # Attempt to cancel the booking
    success = store.cancel_booking(booking_id)
    
    if success:
        query.edit_message_text(
            f"✅ Бронирование #{booking_id} успешно отменено.",
            reply_markup=None
        )
        
        # Show updated bookings list
        all_bookings = store.get_all_bookings()
        
        if all_bookings:
            query.message.reply_text(
                "📋 *Все бронирования:*",
                reply_markup=admin_bookings_keyboard(all_bookings),
                parse_mode='Markdown'
            )
        else:
            query.message.reply_text(
                "В системе нет активных бронирований.",
                reply_markup=admin_menu_keyboard()
            )
            return ADMIN_MENU
    else:
        query.edit_message_text(
            "❌ Не удалось отменить бронирование. Возможно, оно уже было отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return ADMIN_MENU
    
    return VIEWING_ADMIN_BOOKINGS

def admin_reset_all_prompt(update: Update, context: CallbackContext):
    """Prompt for confirmation before resetting all bookings"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "⚠️ *ВНИМАНИЕ!* ⚠️\n\n"
        "Вы собираетесь удалить ВСЕ бронирования из системы.\n"
        "Это действие нельзя отменить.\n\n"
        "Вы уверены?",
        reply_markup=admin_confirm_reset_keyboard(),
        parse_mode='Markdown'
    )
    
    return ADMIN_CONFIRMING_RESET

def admin_reset_all_bookings(update: Update, context: CallbackContext):
    """Reset all bookings in the system"""
    query = update.callback_query
    query.answer()
    
    # Reset bookings in the data store
    store.bookings = {}
    store.user_bookings = {}
    store.booking_counter = 1
    
    query.edit_message_text(
        "✅ Все бронирования успешно удалены из системы.",
        reply_markup=admin_menu_keyboard()
    )
    
    return ADMIN_MENU

# Navigation handlers
def back_to_main(update: Update, context: CallbackContext):
    """Return to main menu"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "Главное меню. Выберите опцию из кнопок ниже.",
        reply_markup=None
    )
    
    return ConversationHandler.END

def back_to_dates(update: Update, context: CallbackContext):
    """Return to date selection"""
    query = update.callback_query
    query.answer()
    
    dates = config.get_date_range()
    
    query.edit_message_text(
        "📅 Выберите дату для бронирования:",
        reply_markup=generate_dates_keyboard(dates)
    )
    
    return SELECTING_DATE

def back_to_bookings(update: Update, context: CallbackContext):
    """Return to bookings list"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    user_bookings = store.get_bookings_for_user(user_id)
    
    query.edit_message_text(
        "🔍 Ваши бронирования:",
        reply_markup=generate_bookings_keyboard(user_bookings)
    )
    
    return VIEWING_BOOKINGS

def back_to_admin(update: Update, context: CallbackContext):
    """Return to admin menu"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "👑 *Панель администратора*\n\n"
        "Выберите действие:",
        reply_markup=admin_menu_keyboard(),
        parse_mode='Markdown'
    )
    
    return ADMIN_MENU

def back_to_admin_bookings(update: Update, context: CallbackContext):
    """Return to admin bookings list"""
    query = update.callback_query
    query.answer()
    
    all_bookings = store.get_all_bookings()
    
    query.edit_message_text(
        "📋 *Все бронирования:*",
        reply_markup=admin_bookings_keyboard(all_bookings),
        parse_mode='Markdown'
    )
    
    return VIEWING_ADMIN_BOOKINGS

def cancel_operation(update: Update, context: CallbackContext):
    """Cancel the current operation and return to main menu"""
    query = update.callback_query
    if query:
        query.answer()
        query.edit_message_text(
            "❌ Операция отменена.\n\n"
            "Вернитесь в главное меню, используя кнопки внизу экрана.",
            reply_markup=None
        )
    else:
        update.message.reply_text(
            "❌ Операция отменена.\n\n"
            "Вернитесь в главное меню, используя кнопки внизу экрана.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END

# Message handler for text buttons
def handle_text_buttons(update: Update, context: CallbackContext):
    """Handle main menu text buttons"""
    text = update.message.text
    
    if text == "📅 Забронировать":
        return start_booking(update, context)
    elif text == "🔍 Мои бронирования":
        return view_my_bookings(update, context)
    elif text == "📋 Все бронирования":
        all_bookings = store.get_all_bookings()
        if not all_bookings:
            update.message.reply_text(
                "В системе нет активных бронирований.",
                reply_markup=main_menu_keyboard()
            )
            return ConversationHandler.END
            
        bookings_text = "📋 *Все бронирования:*\n\n"
        for booking in all_bookings:
            date_parts = booking['date'].split('-')
            display_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
            bookings_text += (
                f"*{display_date} {booking['time']}*\n"
                f"👤 Имя: {booking['name']}\n"
                f"📞 Телефон: {booking['phone']}\n\n"
            )
        
        update.message.reply_text(
            bookings_text,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    elif text == "⏰ Свободное время":
        return view_available_times(update, context)
    elif text == "👤 Админ панель":
        return admin_panel(update, context)
    else:
        update.message.reply_text(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
