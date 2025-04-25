#!/usr/bin/env python3
"""
Окремий скрипт для запуску бота без Flask-інтерфейсу
"""
from bot import start_bot

if __name__ == "__main__":
    print("Starting bot directly...")
    start_bot()