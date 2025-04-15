import logging
import random
import time
import threading
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = '8022971431:AAF60V9KGybtQaVibz_pRKlT5bpLCgHiWtc'
ADMIN_ID = 123456789  # Replace with your Telegram ID

# Store participants & messages
participants = {}
giveaway_end_time = None
giveaway_active = False

# Logger
logging.basicConfig(level=logging.INFO)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Giveaway!\nClick below to participate.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Participate", callback_data="participate")]]
        )
    )

# Participate button handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if not giveaway_active:
        await query.edit_message_text("Giveaway is not active right now.")
        return

    if user.id not in participants:
        participants[user.id] = {'name': user.full_name, 'messages': 1}
        await query.edit_message_text("You’re now entered in the giveaway!")
    else:
        await query.edit_message_text("You already joined!")

# Message tracker
async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if giveaway_active and user.id in participants:
        participants[user.id]['messages'] += 1

# Start giveaway
async def start_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global giveaway_end_time, giveaway_active
    if update.effective_user.id != ADMIN_ID:
        return
    giveaway_active = True
    giveaway_end_time = datetime.now() + timedelta(minutes=1)
    await update.message.reply_text("Giveaway started! Ends in 1 minute!")

    # Timer thread
    threading.Thread(target=run_countdown, args=(context,)).start()

def run_countdown(context):
    global giveaway_active
    while datetime.now() < giveaway_end_time:
        time.sleep(5)
    giveaway_active = False
    context.application.create_task(pick_winner(context))

# Pick random winner with activity weighting
async def pick_winner(context):
    if not participants:
        await context.bot.send_message(ADMIN_ID, "No participants!")
        return

    weighted_list = []
    for user_id, data in participants.items():
        weight = max(1, data['messages'])  # Minimum 1
        weighted_list.extend([user_id] * weight)

    winner_id = random.choice(weighted_list)
    winner_name = participants[winner_id]['name']
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"The giveaway has ended!\nWinner: {winner_name}"
    )
    await context.bot.send_message(
        chat_id=winner_id,
        text="Congratulations! You won the giveaway!"
    )

    # Reset
    participants.clear()

# Entries count
async def show_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Total entries: {len(participants)}")

# Admin-only: force end
async def end_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global giveaway_active, giveaway_end_time
    if update.effective_user.id != ADMIN_ID:
        return
    giveaway_active = False
    giveaway_end_time = datetime.now()
    await update.message.reply_text("Giveaway ended manually.")
    await pick_winner(context)

# Main bot function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("entries", show_entries))
    app.add_handler(CommandHandler("end", end_giveaway))
    app.add_handler(CommandHandler("run", start_giveaway))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_message))

    app.run_polling()

if __name__ == "__main__":
    main()