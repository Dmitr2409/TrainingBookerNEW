import logging
import os
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, Filters
)
from telegram import Bot

from config import TOKEN

# Зберігаємо інформацію про бота
_bot_info = {"username": "your_bot_name"}

def get_bot_info():
    """Отримати інформацію про бота"""
    # Спробуємо отримати актуальну інформацію про бота
    if TOKEN:
        try:
            bot = Bot(TOKEN)
            bot_user = bot.get_me()
            _bot_info["username"] = bot_user.username
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
    
    return _bot_info
from handlers import (
    # Command handlers
    start_command, help_command,
    
    # Booking flow
    start_booking, date_selected, time_selected, name_entered, phone_entered, confirm_booking,
    
    # My bookings
    view_my_bookings, view_booking_details, cancel_booking,
    
    # Available time
    view_available_times,
    
    # Admin panel
    admin_panel, admin_auth, admin_view_all_bookings, admin_view_booking_details,
    admin_cancel_booking, admin_reset_all_prompt, admin_reset_all_bookings,
    
    # Navigation
    back_to_main, back_to_dates, back_to_bookings, back_to_admin, back_to_admin_bookings,
    cancel_operation, handle_text_buttons,
    
    # States
    SELECTING_DATE, SELECTING_TIME, ENTERING_NAME, ENTERING_PHONE,
    CONFIRMING_BOOKING, VIEWING_BOOKINGS, ADMIN_AUTH, ADMIN_MENU,
    VIEWING_ADMIN_BOOKINGS, ADMIN_CONFIRMING_RESET
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Telegram bot"""
    global _bot_info
    
    # Check if token is available
    if not TOKEN:
        logger.error("No Telegram token provided! Set TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN)
    
    # Отримуємо інформацію про бота
    try:
        bot = updater.bot
        bot_user = bot.get_me()
        _bot_info["username"] = bot_user.username
        logger.info(f"Bot username: @{bot_user.username}")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Register booking conversation handler
    booking_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(r'^📅 Забронировать$'), start_booking),
            CallbackQueryHandler(date_selected, pattern=r'^date_')
        ],
        states={
            SELECTING_DATE: [
                CallbackQueryHandler(date_selected, pattern=r'^date_'),
                CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$')
            ],
            SELECTING_TIME: [
                CallbackQueryHandler(time_selected, pattern=r'^time_'),
                CallbackQueryHandler(back_to_dates, pattern=r'^back_to_dates$')
            ],
            ENTERING_NAME: [
                MessageHandler(Filters.text & ~Filters.command, name_entered)
            ],
            ENTERING_PHONE: [
                MessageHandler(Filters.text & ~Filters.command, phone_entered)
            ],
            CONFIRMING_BOOKING: [
                CallbackQueryHandler(confirm_booking, pattern=r'^confirm_booking$'),
                CallbackQueryHandler(cancel_operation, pattern=r'^cancel_operation$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_operation, pattern=r'^cancel_operation$'),
            CommandHandler("start", start_command)
        ],
        name="booking_conversation",
        persistent=False
    )
    dispatcher.add_handler(booking_conv_handler)
    
    # Register my bookings conversation handler
    my_bookings_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(r'^🔍 Мои бронирования$'), view_my_bookings)
        ],
        states={
            VIEWING_BOOKINGS: [
                CallbackQueryHandler(view_booking_details, pattern=r'^view_'),
                CallbackQueryHandler(cancel_booking, pattern=r'^cancel_'),
                CallbackQueryHandler(back_to_bookings, pattern=r'^back_to_bookings$'),
                CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$'),
            CommandHandler("start", start_command)
        ],
        name="my_bookings_conversation",
        persistent=False
    )
    dispatcher.add_handler(my_bookings_conv_handler)
    
    # Register admin panel conversation handler
    admin_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(r'^👤 Админ панель$'), admin_panel)
        ],
        states={
            ADMIN_AUTH: [
                MessageHandler(Filters.text & ~Filters.command, admin_auth)
            ],
            ADMIN_MENU: [
                CallbackQueryHandler(admin_view_all_bookings, pattern=r'^admin_all_bookings$'),
                CallbackQueryHandler(admin_reset_all_prompt, pattern=r'^admin_reset_all$'),
                CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$')
            ],
            VIEWING_ADMIN_BOOKINGS: [
                CallbackQueryHandler(admin_view_booking_details, pattern=r'^admin_view_'),
                CallbackQueryHandler(admin_cancel_booking, pattern=r'^admin_cancel_'),
                CallbackQueryHandler(back_to_admin, pattern=r'^back_to_admin$'),
                CallbackQueryHandler(back_to_admin_bookings, pattern=r'^back_to_admin_bookings$')
            ],
            ADMIN_CONFIRMING_RESET: [
                CallbackQueryHandler(admin_reset_all_bookings, pattern=r'^confirm_reset_all$'),
                CallbackQueryHandler(back_to_admin, pattern=r'^back_to_admin$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$'),
            CommandHandler("start", start_command)
        ],
        name="admin_conversation",
        persistent=False
    )
    dispatcher.add_handler(admin_conv_handler)
    
    # Register available times handler
    dispatcher.add_handler(MessageHandler(
        Filters.regex(r'^⏰ Свободное время$'), 
        view_available_times
    ))
    
    # Register text button handler for main menu buttons
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, 
        handle_text_buttons
    ))
    
    # Start the Bot
    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    start_bot()
