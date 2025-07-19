# 🔥 Auto UTR Premium Telegram Bot

A Telegram bot that manages premium group access via PhonePe UTR payments with automatic user removal when subscriptions expire.

## ✨ Features

- Accepts UTR payments via PhonePe gateway
- Three subscription plans: ₹3 (weekly), ₹10 (monthly), ₹99 (yearly)
- Automatically sends premium group invite after payment verification
- Removes users when subscription expires
- MongoDB database for user management
- Ready for deployment on Render (free tier)

## 🤖 Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Show main menu with options | All users |
| `/help`  | Show help information | All users |
| `/status` | Check your subscription status | All users |
| `/plans` | View available premium plans | All users |
| `/adminstats` | Get bot statistics (messages, users, etc.) | Owner only |
| `/broadcast` | Send message to all users | Owner only |

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- PhonePe Merchant Account

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/auto-premium-bot.git
   cd auto-premium-bot
