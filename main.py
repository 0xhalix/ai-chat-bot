import asyncio
import logging
import datetime
import telegram as tg
from telegram.ext import (ApplicationBuilder,
                          ContextTypes,
                          CommandHandler,
                          MessageHandler,
                          ConversationHandler, 
                          filters)
import os
from dotenv import load_dotenv as load_env

load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level= logging.INFO
)
logger = logging.getLogger(__name__)

# effective_chat
# effective_user
# effective_sender
# effective_message


async def start(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= "Hello. \nI'm a bot, please talk to me!")

async def any_message(update:tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id= update.effective_chat.id, text= 'You sent me a message')

async def ai_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nInitiate Ai guided chat")
    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👨\u200d💻')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    try:
        await context.bot.send_message(chat_id=update.effective_user.id, text= 'Initializing Ai chat bot, Start your conversation below')
        print("AI chat initialization Started")
    except tg.error.NetworkError as error:
        print(f"Message Error: {error}")

async def end_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nEnd Chat Triggered by user")
    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👨\u200d💻')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    
    try:
        await context.bot.send_message(chat_id=update.effective_user.id, text= 'AI chat session successfully ended.')
        print("AI Chat session Ended")
    except tg.error.NetworkError as error:
        print(f"Message Error: {error}")
        await context.bot.send_message(chat_id=update.effective_user.id, text= f'Failed to end chat session, Try again: {update.effective_message.text}')

async def unknown(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= f"Sorry, I do not understand the command {update.effective_message.text}")


# CONVERSATION BOT
GENDER, PHOTO, LOCATION, BIO = range(4)
async def conversation(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Boy", "Girl"]]

    await update.effective_message.reply_text(
        f"""Hi there, I'm your Ai chat bot.\nSend /cancel to stop the conversation.\n\nAre you a boy or a girl?""", 
        reply_markup=tg.ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            input_field_placeholder="Boy or girl?"
        ),
        do_quote=True
    )
    return GENDER

async def gender(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Gender of {user.first_name}: {update.effective_message.text}")
    await update.effective_message.reply_text(
        f"""I see! Please send me a photo of yourself,\nso i know what you look like, or send /skip if you don't want to""",
        reply_markup=tg.ReplyKeyboardRemove(),
        do_quote=True
    )
    return PHOTO

async def photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.effective_message.photo[-1].get_file()
    photo_name = f"{user.username}.jpg"
    await photo_file.download_to_drive(photo_name)
    logger.info(f"Photo of {user.first_name}: {photo_name}")
    await update.message.reply_text(
        f"Great! Now, send me your location please,\nor send /skip if you don't want to.",
        do_quote=True
    )

    return LOCATION

async def skip_photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a photo.")
    await update.effective_message.reply_text(
        f"I bet you look great! Now, send me your location please, or send /skip.",
        do_quote=True
    )

    return LOCATION

async def location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_location = update.effective_message.location
    print(update.effective_message.location)
    logger.info(f"Location of {user.first_name}: {user_location.latitude} / {user_location.longitude}")
    await update.message.reply_text(
        f"Super, lastly\n tell me something about yourself.",
        do_quote=True
    )
    return BIO

async def skip_location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a location.")
    await update.effective_message.reply_text(
        f"That's not a problem. But, can you tell me something about yourself?",
        do_quote=True
    )

    return BIO

async def bio(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"Bio of {user.first_name}: {update.effective_message.text}")
    await update.effective_message.reply_text(
        f"Thank You!\nI hope we can chat again some day.",
        do_quote=True
    )
    return ConversationHandler.END

async def cancel(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"user {user.first_name} canceled the conversation")
    await update.effective_message.reply_text(
        f"Bye!\nI hope we can talk again.",
        do_quote=True,
        reply_markup=tg.ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, any_message)
    aichat_handler = CommandHandler('ai_chat', ai_chat)
    endchat_handler = CommandHandler('end_chat', end_chat)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    
    # Converstion Handler
    conversation_handler= ConversationHandler(
        entry_points=[CommandHandler('converse', conversation)],
        states={
            GENDER: [MessageHandler(filters.Regex("(?i)^(Boy|Girl|Other)$"), gender)],
            PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("skip", skip_photo)],
            LOCATION: [MessageHandler(filters.LOCATION, location), CommandHandler("skip", skip_location)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conversation_handler)
    application.add_handler(aichat_handler)
    application.add_handler(endchat_handler)
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    application.add_handler(unknown_handler)

    try:
        application.run_polling(timeout= datetime.timedelta(seconds=15), bootstrap_retries= 3)
    except tg.error.TimedOut as error:
        print(f"Start-Up error: {error}")
    except tg.error.NetworkError as net_error:
        print(f"Network Error: {net_error}")


if __name__ == '__main__':
    main()