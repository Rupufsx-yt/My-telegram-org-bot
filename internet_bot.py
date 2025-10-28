#!/usr/bin/env python3
"""
INTERNET SELL APP BOT - RENDER FIXED VERSION
"""

import os
import sqlite3
import logging
import secrets
import string
import asyncio
from threading import Thread
from flask import Flask

# Flask app for Render port binding
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8319114937:AAFFIwvLP3FHtJmMJ-C-9ILQ3U-oFfAdOGk')
CHANNEL_LINK = "https://t.me/+kTvYd3_mSbs2MWNl"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

class InternetBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_database()
        self.setup_handlers()
        print("🤖 Bot initialized successfully!")
    
    def setup_database(self):
        """Database setup"""
        try:
            self.conn = sqlite3.connect('/tmp/internet_bot.db', check_same_thread=False)
            cursor = self.conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_channel BOOLEAN DEFAULT FALSE,
                    referral_code TEXT UNIQUE,
                    referral_count INTEGER DEFAULT 0,
                    balance INTEGER DEFAULT 0,
                    app_access BOOLEAN DEFAULT FALSE,
                    withdrawal_access BOOLEAN DEFAULT FALSE
                )
            ''')
            
            self.conn.commit()
            print("✅ Database setup complete!")
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def setup_handlers(self):
        """Setup bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("app", self.app_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        print("✅ Handlers setup complete!")
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
            if not cursor.fetchone():
                return code
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_id = update.effective_user.id
            first_name = update.effective_user.first_name
            
            # Register user
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                referral_code = self.generate_referral_code()
                cursor.execute(
                    "INSERT INTO users (user_id, first_name, referral_code) VALUES (?, ?, ?)",
                    (user_id, first_name, referral_code)
                )
                self.conn.commit()
            
            # Show welcome message
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = """
🤖 **Welcome to Internet Sell App Bot!**

💰 **Earn Money by Selling Internet:**
• 500MB Internet Sell = ₹100
• 1GB Internet Sell = ₹200

🎯 **Requirements:**
1. Join our channel
2. Refer 10 friends
3. Get app download link
4. **Withdrawal after 10 referrals only**

👥 **Referral Program:**
• ₹15 per successful referral
• Minimum 10 referrals for app access
• UPI withdrawal available

👇 Join channel to start!
            """
            
            await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            print(f"Start error: {e}")
            await update.message.reply_text("❌ Error occurred. Please try again.")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "verify_join":
                await self.verify_channel_join(query, context)
            elif query.data == "get_referral":
                await self.show_referral_info(query, context)
            elif query.data == "check_balance":
                await self.show_balance(query, context)
            elif query.data == "get_app_link":
                await self.get_app_link(query, context)
            elif query.data == "withdraw_earnings":
                await self.withdraw_earnings(query, context)
                
        except Exception as e:
            print(f"Button error: {e}")
    
    async def verify_channel_join(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Verify channel join"""
        user_id = query.from_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET joined_channel = TRUE WHERE user_id = ?", (user_id,))
        self.conn.commit()
        
        keyboard = [
            [InlineKeyboardButton("📤 Get Referral Link", callback_data="get_referral")],
            [InlineKeyboardButton("💰 Check Balance", callback_data="check_balance")],
            [InlineKeyboardButton("🎁 Get App Link", callback_data="get_app_link")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
✅ **Channel Join Verified!**

🎉 **Welcome to Internet Sell App Program!**

💰 **Earning Plan:**
• 500MB Internet Sell = ₹100
• 1GB Internet Sell = ₹200
• ₹15 per referral

🎯 **Complete 10 referrals to get:**
• Internet Sell App download
• Withdrawal access

👇 Choose an option below:
        """
        
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_referral_info(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show referral info"""
        user_id = query.from_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT referral_code, referral_count, withdrawal_access FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        referral_code = user_data[0]
        referral_count = user_data[1]
        withdrawal_access = user_data[2]
        
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        withdrawal_status = "✅ Available" if withdrawal_access else f"❌ Need {10 - referral_count} more"
        
        message_text = f"""
📤 **Your Referral System**

🔗 **Your Link:**
`{referral_link}`

📊 **Referrals:** {referral_count}/10
💰 **Earnings:** ₹{referral_count * 15}
💸 **Withdrawal:** {withdrawal_status}

🎯 **Complete 10 referrals for withdrawal access!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="verify_join")],
            [InlineKeyboardButton("📢 Share", url=f"https://t.me/share/url?url={referral_link}&text=Join%20Internet%20Sell%20App!")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_balance(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show balance"""
        user_id = query.from_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance, referral_count, withdrawal_access FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        balance = user_data[0]
        referral_count = user_data[1]
        withdrawal_access = user_data[2]
        
        withdrawal_status = "✅ Available" if withdrawal_access else f"❌ Need {10 - referral_count} more"
        
        message_text = f"""
💰 **Your Earnings**

📊 **Balance:** ₹{balance}
👥 **Referrals:** {referral_count}/10
💵 **Earnings:** ₹{referral_count * 15}
💸 **Withdrawal:** {withdrawal_status}

🎯 **Complete 10 referrals for withdrawal!**
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="verify_join")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def get_app_link(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Provide app link"""
        user_id = query.from_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        referral_count = user_data[0]
        
        if referral_count >= 10:
            app_link = "https://example.com/internet-sell-app.apk"  # Replace with actual link
            
            message_text = f"""
🎉 **Congratulations!**

📲 **Download App:**
{app_link}

💰 **Start Selling:**
• 500MB = ₹100
• 1GB = ₹200

📊 **Your Referrals:** {referral_count}
💸 **Withdrawal:** ✅ Available
            """
            
            await query.edit_message_text(message_text, parse_mode='Markdown')
        else:
            remaining = 10 - referral_count
            await query.edit_message_text(
                f"❌ **Need {remaining} more referrals!**\n\n"
                f"Complete {remaining} referrals to get app download link.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Get Referral Link", callback_data="get_referral")],
                    [InlineKeyboardButton("🔙 Back", callback_data="verify_join")]
                ])
            )
    
    async def withdraw_earnings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle withdrawal"""
        user_id = query.from_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance, referral_count, withdrawal_access FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        balance = user_data[0]
        referral_count = user_data[1]
        withdrawal_access = user_data[2]
        
        if not withdrawal_access:
            remaining = 10 - referral_count
            await query.edit_message_text(
                f"❌ **Withdrawal Not Available!**\n\n"
                f"📊 **Referrals:** {referral_count}/10\n"
                f"🎯 **Need {remaining} more for withdrawal access**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Get Referral Link", callback_data="get_referral")],
                    [InlineKeyboardButton("🔙 Back", callback_data="verify_join")]
                ])
            )
            return
        
        if balance >= 50:
            await query.edit_message_text(
                f"💸 **Withdrawal Available!**\n\n"
                f"💰 **Balance:** ₹{balance}\n\n"
                f"Send: `/withdraw your_upi_id`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ **Minimum ₹50 required!**\n\n"
                f"💰 **Current Balance:** ₹{balance}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="verify_join")]
                ])
            )
    
    # Command handlers
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /referral command"""
        await self.show_referral_info(update, context)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        await self.show_balance(update, context)
    
    async def app_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /app command"""
        await self.get_app_link(update, context)
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /withdraw command"""
        user_id = update.effective_user.id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance, withdrawal_access FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data or not user_data[1]:
            await update.message.reply_text("❌ Complete 10 referrals for withdrawal access!")
            return
        
        if context.args:
            upi_id = context.args[0]
            balance = user_data[0]
            
            cursor.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
            self.conn.commit()
            
            await update.message.reply_text(
                f"✅ **Withdrawal Request Submitted!**\n\n"
                f"💰 **Amount:** ₹{balance}\n"
                f"📱 **UPI ID:** {upi_id}\n"
                f"⏰ **Processing:** 24 hours\n\n"
                f"Contact support for queries."
            )

def start_bot():
    """Start the Telegram bot"""
    print("🚀 Starting Telegram Bot...")
    try:
        bot = InternetBot(BOT_TOKEN)
        print("✅ Bot setup complete. Starting polling...")
        bot.application.run_polling()
    except Exception as e:
        print(f"❌ Bot failed: {e}")

if __name__ == '__main__':
    print("🤖 Starting Internet Sell Bot on Render...")
    
    # Start Flask server in a separate thread for port binding
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Flask server started on port 5000")
    
    # Start Telegram bot
    start_bot()
