import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    JobQueue
)
from datetime import datetime, timedelta
from config import config
from database import Database
from payment import PhonePePayment
import pytz

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
payment_gateway = PhonePePayment()

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💰 Buy Premium", callback_data='select_plan')],
        [InlineKeyboardButton("🔍 Check Status", callback_data='check_status')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"👋 Welcome *{user.first_name}*!\n\n"
        "This bot provides access to premium content groups. "
        "Choose an option below:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def select_plan(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Weekly - ₹3", callback_data='plan_weekly')],
        [InlineKeyboardButton("Monthly - ₹10", callback_data='plan_monthly')],
        [InlineKeyboardButton("Yearly - ₹99", callback_data='plan_yearly')],
        [InlineKeyboardButton("« Back", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="📊 *Select a Premium Plan*\n\n"
             "• Weekly: ₹3 (7 days)\n"
             "• Monthly: ₹10 (30 days)\n"
             "• Yearly: ₹99 (365 days)\n\n"
             "Choose your plan:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def initiate_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    plan_type = query.data.split('_')[1]
    
    amount = config.PLANS[plan_type]
    user_id = query.from_user.id
    
    # Generate payment link
    payment_url = payment_gateway.generate_payment_link(
        user_id=user_id,
        amount=amount,
        plan=plan_type
    )
    
    if payment_url:
        # Store transaction in database
        transaction_id = f"TXN{user_id}{int(datetime.now().timestamp())}"
        db.transactions.insert_one({
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount,
            "plan": plan_type,
            "status": "PENDING",
            "created_at": datetime.now()
        })
        
        keyboard = [
            [InlineKeyboardButton("💳 Pay Now", url=payment_url)],
            [InlineKeyboardButton("✅ I've Paid", callback_data=f'verify_{transaction_id}')],
            [InlineKeyboardButton("« Back", callback_data='select_plan')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            text=f"🔔 *{plan_type.capitalize()} Plan - ₹{amount/100}*\n\n"
                 "1. Click *Pay Now* to complete payment\n"
                 "2. After payment, click *I've Paid* and send your UTR number\n"
                 "3. We'll verify and add you to the premium group",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        query.edit_message_text(text="⚠️ Payment initiation failed. Please try again later.")

def verify_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    transaction_id = query.data.split('_')[1]
    
    query.edit_message_text(
        text="📩 Please send your *UTR number* from the payment receipt.\n\n"
             "Example: `UTR1234567890`",
        parse_mode='Markdown'
    )
    
    # Store transaction ID in user data for next message handler
    context.user_data['pending_transaction'] = transaction_id

def handle_utr(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    utr_number = update.message.text.strip()
    
    if 'pending_transaction' not in context.user_data:
        update.message.reply_text("No pending payment verification. Use /start to begin.")
        return
    
    transaction_id = context.user_data['pending_transaction']
    transaction = db.transactions.find_one({"transaction_id": transaction_id})
    
    if not transaction:
        update.message.reply_text("❌ Transaction not found. Please start over.")
        return
    
    # In a real implementation, verify UTR with PhonePe API
    # For demo, we'll assume payment is successful
    plan = transaction['plan']
    expiry_days = {
        'weekly': 7,
        'monthly': 30,
        'yearly': 365
    }.get(plan, 30)
    
    expiry_date = datetime.now() + timedelta(days=expiry_days)
    
    # Update user in database
    db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "plan": plan,
            "expiry_date": expiry_date,
            "joined_at": datetime.now(),
            "status": "ACTIVE"
        }},
        upsert=True
    )
    
    # Update transaction status
    db.transactions.update_one(
        {"transaction_id": transaction_id},
        {"$set": {
            "utr_number": utr_number,
            "status": "COMPLETED",
            "verified_at": datetime.now()
        }}
    )
    
    # Send premium group link
    update.message.reply_text(
        f"🎉 *Payment Verified!*\n\n"
        f"🔗 [Join Premium Group]({config.PREMIUM_GROUP_LINK})\n"
        f"📅 Expiry: {expiry_date.strftime('%d %b %Y')}\n\n"
        "You'll be automatically removed when your subscription ends.",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    # Clear pending transaction
    del context.user_data['pending_transaction']

def check_status(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    user = db.users.find_one({"user_id": user_id})
    
    if user and user.get('status') == "ACTIVE":
        expiry_date = user['expiry_date'].strftime('%d %b %Y')
        query.edit_message_text(
            text=f"✅ *Active Subscription*\n\n"
                 f"📋 Plan: {user['plan'].capitalize()}\n"
                 f"📅 Expiry: {expiry_date}\n\n"
                 f"🔗 [Premium Group]({config.PREMIUM_GROUP_LINK})",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        keyboard = [[InlineKeyboardButton("💰 Buy Premium", callback_data='select_plan')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="❌ *No Active Subscription*\n\n"
                 "You don't have an active premium subscription. "
                 "Purchase one to access premium content.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def remove_expired_users(context: CallbackContext):
    now = datetime.now()
    expired_users = db.users.find({
        "expiry_date": {"$lt": now},
        "status": "ACTIVE"
    })
    
    for user in expired_users:
        try:
            # Remove from group
            context.bot.kick_chat_member(
                chat_id=config.PREMIUM_GROUP_ID,
                user_id=user['user_id']
            )
            
            # Notify user
            context.bot.send_message(
                chat_id=user['user_id'],
                text="⚠️ *Your Premium Access Has Expired*\n\n"
                     "Your subscription has ended. Renew to regain access "
                     "to the premium group.",
                parse_mode='Markdown'
            )
            
            # Update status in DB
            db.users.update_one(
                {"user_id": user['user_id']},
                {"$set": {"status": "EXPIRED"}}
            )
            
            logger.info(f"Removed expired user: {user['user_id']}")
            
        except Exception as e:
            logger.error(f"Failed to remove user {user['user_id']}: {e}")

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    
    if update.effective_message:
        update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again later."
        )

def main():
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(select_plan, pattern='^select_plan$'))
    dp.add_handler(CallbackQueryHandler(initiate_payment, pattern='^plan_'))
    dp.add_handler(CallbackQueryHandler(verify_payment, pattern='^verify_'))
    dp.add_handler(CallbackQueryHandler(check_status, pattern='^check_status$'))
    dp.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_utr))
    
    # Error handler
    dp.add_error_handler(error_handler)
    
    # Job queue for removing expired users (runs daily at midnight IST)
    job_queue = updater.job_queue
    time_ist = pytz.timezone('Asia/Kolkata').localize(datetime.strptime("00:00", "%H:%M")).time()
    job_queue.run_daily(remove_expired_users, time=time_ist)
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started and running...")
    updater.idle()

if __name__ == '__main__':
    main()
