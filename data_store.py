from datetime import datetime
import logging
import os
from flask import current_app

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Клас для роботи з даними
class DataStore:
    def __init__(self):
        # Dictionary to store bookings: {booking_id: {date, time, user_id, name, phone}}
        self.bookings = {}
        # Dictionary to track booking IDs by user: {user_id: [booking_id1, booking_id2, ...]}
        self.user_bookings = {}
        # Counter for generating unique booking IDs
        self.booking_counter = 1
        # Dictionary to store user states during conversations: {user_id: {state, data}}
        self.user_states = {}
        # Dictionary to track admin authentications: {user_id: is_authenticated}
        self.admin_auth = {}
        
        logger.info("DataStore initialized")
    
    def add_booking(self, user_id, date, time, name, phone):
        """Add a new booking to the store"""
        booking_id = self.booking_counter
        self.booking_counter += 1
        
        # Store booking details
        self.bookings[booking_id] = {
            'id': booking_id,
            'date': date,
            'time': time,
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to user's bookings list
        if user_id not in self.user_bookings:
            self.user_bookings[user_id] = []
        self.user_bookings[user_id].append(booking_id)
        
        logger.info(f"Added booking {booking_id} for user {user_id} on {date} at {time}")
        return booking_id
    
    def get_bookings_for_user(self, user_id):
        """Get all bookings for a specific user"""
        booking_ids = self.user_bookings.get(user_id, [])
        result = []
        for bid in booking_ids:
            if bid in self.bookings:
                result.append(self.bookings[bid])
        return result
    
    def get_all_bookings(self):
        """Get all bookings in the system"""
        return list(self.bookings.values())
    
    def cancel_booking(self, booking_id):
        """Cancel a booking by ID"""
        if booking_id not in self.bookings:
            return False
        
        user_id = self.bookings[booking_id]['user_id']
        if user_id in self.user_bookings and booking_id in self.user_bookings[user_id]:
            self.user_bookings[user_id].remove(booking_id)
        
        del self.bookings[booking_id]
        logger.info(f"Cancelled booking {booking_id}")
        return True
    
    def is_time_slot_available(self, date, time):
        """Check if a time slot is available"""
        for bid, booking in self.bookings.items():
            if booking['date'] == date and booking['time'] == time:
                return False
        return True
    
    def get_available_slots(self, date, available_times):
        """Get available time slots for a specific date"""
        available_slots = []
        
        for time in available_times:
            if self.is_time_slot_available(date, time):
                available_slots.append(time)
        
        return available_slots
    
    def set_user_state(self, user_id, state, data=None):
        """Set the current state for a user in a conversation"""
        if data is None:
            data = {}
        self.user_states[user_id] = {'state': state, 'data': data}
    
    def get_user_state(self, user_id):
        """Get the current state for a user"""
        return self.user_states.get(user_id, {'state': None, 'data': {}})
    
    def clear_user_state(self, user_id):
        """Clear the state for a user"""
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def authenticate_admin(self, user_id, is_authenticated=True):
        """Set admin authentication status"""
        self.admin_auth[user_id] = is_authenticated
        logger.info(f"Admin {user_id} authentication set to {is_authenticated}")
    
    def is_admin_authenticated(self, user_id):
        """Check if a user is authenticated as admin"""
        # Перевірка, чи користувач є в списку адміністраторів з конфігурації
        if hasattr(current_app, 'config') and user_id in current_app.config.get('ADMIN_IDS', []):
            return True
            
        return self.admin_auth.get(user_id, False)

# Create a global instance of the data store
store = DataStore()
