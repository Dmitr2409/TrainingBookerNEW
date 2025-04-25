import os
import sys
from flask import Flask, render_template
from bot import start_bot, get_bot_info
import threading

# Create Flask app
app = Flask(__name__)

# Add admin ID to config
app.config['ADMIN_IDS'] = [1006518993]

@app.route('/')
def index():
    """Main page"""
    bot_info = get_bot_info()
    return render_template('index.html', bot_username=bot_info.get('username', 'your_bot_name'))

def run_bot():
    """Run bot in a separate thread"""
    start_bot()

if __name__ == "__main__":
    # Get current run mode from command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else 'web'

    if mode == 'bot':
        # Run only bot
        print("Starting bot in bot-only mode...")
        start_bot()
    elif mode == 'both':
        # Run both web app and bot
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        app.run(host='0.0.0.0', port=8080)
    else:
        # Run only web app
        app.run(host='0.0.0.0', port=8080)