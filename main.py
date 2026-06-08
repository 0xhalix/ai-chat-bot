import asyncio
import logging
import telegram as tg
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv as load_env

load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level= logging.INFO
)

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
        await context.bot.send_message(chat_id=update.effective_user.id, text= 'Failed to end chat session, Try again: {update.effective_message.text}')



async def unknown(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= f"Sorry, I do not understand the command {update.effective_message.text}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.Text('Hi'), any_message)
    aichat_handler = CommandHandler('ai_chat', ai_chat)
    endchat_handler = CommandHandler('end_chat', end_chat)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)


    application.add_handler(aichat_handler)
    application.add_handler(endchat_handler)
    application.add_handler(unknown_handler)
    application.add_handler(start_handler)
    application.add_handler(message_handler)

    try:
        application.run_polling()
    except tg.error.TimedOut as error:
        print(f"Start-Up error: {error}")
    except tg.error.NetworkError as net_error:
        print(f"Network Error: {net_error}")