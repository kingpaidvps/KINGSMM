from keep_alive import keep_alive
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import qrcode

# Your Bot Token and other IDs
BOT_TOKEN = "7913902351:AAHWkIoL0FyOcODRjcmSl0gAN_fdCYAgSlw"
ADMIN_GROUP_ID = -1002261062059
ADMIN_ID = 5027022179
CHANNEL_ID = -1001234567890
UPI_ID = "dharmendra-kingvip@fam"

# Service Prices
PRICES = {
    "followers": 300,
    "likes": 20,
    "youtube_views": 50,
    "youtube_likes": 50,
    "instagram_views": 10
}

WAITING_FOR_QUANTITY, WAITING_FOR_LINK = range(2)

# Function to generate UPI QR Code
def generate_qr_code(user_id, amount):
    payment_url = f"upi://pay?pa={UPI_ID}&pn=SMMPanel&am={amount}&cu=INR"
    qr = qrcode.make(payment_url)
    qr_path = f"qr_{user_id}.png"
    qr.save(qr_path)
    return qr_path

# Start Command
def start(update: Update, context: CallbackContext):
    keyboard = [
        ["🌸 Buy Instagram Followers", "❤️ Buy Instagram Likes"],
        ["📈 Buy YouTube Views", "👍 Buy YouTube Likes"],
        ["👀 Buy Instagram Views", "📞 Support"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("💡 Welcome to the best SMM Panel! Choose a service:", reply_markup=reply_markup)

# Step 1: Ask for Quantity
def buy_service(update: Update, context: CallbackContext):
    service = update.message.text
    services_map = {
        "🌸 Buy Instagram Followers": "followers",
        "❤️ Buy Instagram Likes": "likes",
        "📈 Buy YouTube Views": "youtube_views",
        "👍 Buy YouTube Likes": "youtube_likes",
        "👀 Buy Instagram Views": "instagram_views"
    }
    if service in services_map:
        context.user_data["service"] = services_map[service]
        update.message.reply_text("📌 Enter the number of units you want:")
        return WAITING_FOR_QUANTITY
    return ConversationHandler.END

# Step 2: Ask for Link
def ask_for_link(update: Update, context: CallbackContext):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            update.message.reply_text("❌ Please enter a valid quantity.")
            return WAITING_FOR_QUANTITY
    except ValueError:
        update.message.reply_text("❌ Please enter a valid number.")
        return WAITING_FOR_QUANTITY

    context.user_data["quantity"] = quantity
    update.message.reply_text("🔗 Now, send your video/reel/post link:")
    return WAITING_FOR_LINK

# Step 3: Show Payment Details & QR Code
def show_payment_details(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link = update.message.text
    context.user_data["link"] = link
    quantity = context.user_data["quantity"]
    service = context.user_data["service"]
    amount = round((quantity / 1000) * PRICES[service], 2)
    context.user_data["amount"] = amount

    qr_path = generate_qr_code(user_id, amount)

    update.message.reply_photo(
        photo=open(qr_path, "rb"),
        caption=f"✅ Order Details:\n\n📌 Service: {service.replace('_', ' ').title()}\n📊 Quantity: {quantity}\n💰 Amount: ₹{amount}\n\n📸 Please scan the QR code and send the payment screenshot."
    )

    os.remove(qr_path)
    return ConversationHandler.END

# Forward Screenshot to Admin and Notify Channel
def forward_screenshot(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username or "No Username"
    amount = context.user_data.get("amount", "Unknown")
    link = context.user_data.get("link", "Hidden")
    quantity = context.user_data.get("quantity", "Unknown")
    service = context.user_data.get("service", "Unknown").replace('_', ' ').title()

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_caption = (f"📥 New Payment Received!\n\n"
                     f"👤 User: @{username}\n"
                     f"🔗 Link: {link}\n"
                     f"📊 Quantity: {quantity} {service}\n"
                     f"💰 Amount: ₹{amount}")

    context.bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=update.message.photo[-1].file_id, caption=admin_caption, reply_markup=reply_markup)

    channel_caption = (f"🚀 *New Order Received!*\n\n"
                       f"👤 User: @{username}\n"
                       f"📊 Quantity: {quantity} {service}\n"
                       f"💰 Amount: ₹{amount}\n"
                       f"✅ Order is being processed...")
    context.bot.send_message(chat_id=CHANNEL_ID, text=channel_caption, parse_mode="Markdown")
    update.message.reply_text("✅ Screenshot forwarded! Please wait for admin approval.")

# Admin Approval Handler
def handle_admin_response(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        context.bot.send_message(user_id, "✅ Payment approved! Your order is being processed.")
        query.edit_message_text("✅ Order approved successfully!")
    elif action == "reject":
        context.bot.send_message(user_id, "❌ Payment rejected. Please try again or contact support.")
        query.edit_message_text("❌ Payment rejected.")

# Main Function
def main():
    keep_alive()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex("^(🌸 Buy Instagram Followers|❤️ Buy Instagram Likes|📈 Buy YouTube Views|👍 Buy YouTube Likes|👀 Buy Instagram Views)$"), buy_service)],
        states={
            WAITING_FOR_QUANTITY: [MessageHandler(Filters.text & ~Filters.command, ask_for_link)],
            WAITING_FOR_LINK: [MessageHandler(Filters.text & ~Filters.command, show_payment_details)],
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.photo, forward_screenshot))
    dp.add_handler(CallbackQueryHandler(handle_admin_response))
    dp.add_handler(MessageHandler(Filters.regex("📞 Support"), lambda u, c: u.message.reply_text("📞 Contact @KingVipOwner")))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()