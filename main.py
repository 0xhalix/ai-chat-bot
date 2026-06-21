import asyncio
import logging
import datetime
import os
from typing import Optional
import telegram as tg
from pathlib import Path
from telegram.ext import (ApplicationBuilder,
                          ContextTypes,
                          CommandHandler,
                          MessageHandler,
                          ConversationHandler, 
                          filters)
from dotenv import load_dotenv as load_env

IMAGE_PATH = Path(__file__).resolve().parents[0] / "images" / "conversations"
IMAGE_PATH.mkdir(parents=True, exist_ok=True)
load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_TIMEOUT_SEC = 120
GEMINI_MAX_TRIES = 2
SAFE_MSG_LIMIT = 3800

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level= logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    
    user = update.effective_user
    if user and user.first_name:
        name = user.first_name
    elif user and user.username:
        name = f"@{user.username}"
    else:
        name = "there"
        
    msg = (
        f"Hey {name}, welcome to the AI Chat Bot! 👋\n\n"
        "Chat with our AI assistant in a simple, fast, and structured way. "
        "Use it to ask questions, explore ideas, and have full conversations powered by the backend model.\n\n"
        "To get started, complete the onboarding flow first, then begin chatting when access is enabled.\n\n"
        "Available commands:\n"
        "  /converse — Start the onboarding conversation\n"
        "  /cancel — Cancel the current onboarding flow\n"
        "  /ai_chat — Start an AI chat session\n"
        "  /end_chat — End the current AI chat session\n"
        "  /id — Show your Telegram user ID\n"
        "  /help — View all available commands\n\n"
        "Once you are set up, you can start chatting anytime."
    )
    
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= msg)

async def any_message(update:tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id= update.effective_chat.id, text= 'You sent me a message')

async def unknown(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= f"Sorry, I do not understand the command {update.effective_message.text}")

async def user_id(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}, equested for ID\nUser ID: {update.effective_user.id}")
    await update.effective_message.reply_text(text= f"Your user ID is {update.effective_user.id}", do_quote= True)

async def help(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "AI Chat Bot — Command Reference\n\n"
        "Getting Started\n"
        "• /converse — Begin the onboarding process\n"
        "• /cancel — Cancel the current onboarding process\n\n"
        "AI Chat\n"
        "• /ai_chat — Start a new AI chat session\n"
        "• /end_chat — End your current AI chat session\n\n"
        "Utility\n"
        "• /id — Display your Telegram user ID\n"
        "• /help — Show this command reference\n"
        "• /start — Show the welcome message\n"
    )
    await update.effective_message.reply_text(text=msg, do_quote=True)

# CONVERSATION BOT
GENDER, PHOTO, LOCATION, BIO = range(4)
async def conversation(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Boy", "Girl"]]

    await update.effective_message.reply_text(
        text= f"""Hi there, I'm your Ai chat bot.\nSend /cancel to stop the conversation.\n\nAre you a boy or a girl?""", 
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
        text= f"""I see! Please send me a photo of yourself,\nso i know what you look like, or send /skip if you don't want to""",
        reply_markup=tg.ReplyKeyboardRemove(),
        do_quote=True
    )
    return PHOTO

async def photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.effective_message.photo[-1].get_file()
    photo_name = f"{user.username}.jpg"
    file_path = IMAGE_PATH / photo_name
    await photo_file.download_to_drive(file_path)
    logger.info(f"Photo of {user.first_name}: {photo_name}")
    await update.message.reply_text(
        text= f"Great! Now, send me your location please,\nor send /skip if you don't want to.",
        do_quote=True
    )

    return LOCATION

async def skip_photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a photo.")
    await update.effective_message.reply_text(
        text= f"I bet you look great! Now, send me your location please, or send /skip.",
        do_quote=True
    )

    return LOCATION

async def location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_location = update.effective_message.location
    print(update.effective_message.location)
    logger.info(f"Location of {user.first_name}: {user_location.latitude} / {user_location.longitude}")
    await update.message.reply_text(
        text= f"Super, lastly\n tell me something about yourself.",
        do_quote=True
    )
    return BIO

async def skip_location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a location.")
    await update.effective_message.reply_text(
        text= f"That's not a problem. But, can you tell me something about yourself?",
        do_quote=True
    )

    return BIO

async def bio(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"Bio of {user.first_name}: {update.effective_message.text}")
    await update.effective_message.reply_text(
        text= f"Thank You!\nI hope we can chat again some day.",
        do_quote=True
    )
    return ConversationHandler.END

async def cancel(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"user {user.first_name} canceled the conversation")
    await update.effective_message.reply_text(
        text= f"Bye!\nI hope we can talk again.",
        do_quote=True,
        reply_markup=tg.ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Conversation Handler for AI chat bot
RESPONSE = range(1)
async def ai_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nInitiate Ai guided chat")

    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👨\u200d💻')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    
    try:
        await update.effective_message.reply_text(
            text= f"""Initializing Ai chat bot, Start your conversation below.\n\nSend /end_chat to end the chat session.""", 
            do_quote=True
        )
        print(f"AI chat initialization by User: @{update.effective_user.username} Started")
    except tg.error.TelegramError as error:
        print(f'Message Error: {error}')
        
    return RESPONSE
        
async def response(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    gemini_key: Optional[str] = os.getenv("GEMINI_KEY")
    print(f"User_prompt: {update.effective_message.text}")
    prompt = update.effective_message.text if update.effective_message.text else ""
    
    def _call_gemini_sync(prompt: str, api_key: str) -> Optional[str]:
        """Sync Gemini call. Runs inside executor. Returns text or None."""
        try:
            import google.genai as genai 
            client = genai.Client(api_key=api_key)
            gen_config = None
            
            try:
                from google.genai import types as genai_types
                gen_config = genai_types.GenerateContentConfig(thinking_config=genai_types.ThinkingConfig(thinking_level="high"))
            except Exception as e:
                print(e)

            kwargs: dict = {
                "model": GEMINI_MODEL,
                "contents": prompt,
            }
            if gen_config is not None:
                kwargs["config"] = gen_config

            response = client.models.generate_content(**kwargs)
            print(f"response = {response.text[:50]}")
            
        
            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()
            logger.warning("Gemini returned empty text")
            return None
        except Exception as exc:
            logger.warning(f"Gemini sync call failed: {exc}")
            return None


    async def _call_gemini(prompt: str, api_key: str) -> Optional[str]:
        """Async wrapper for Gemini. Up to GEMINI_MAX_TRIES attempts."""
        loop = asyncio.get_event_loop()
        for attempt in range(1, GEMINI_MAX_TRIES + 1):
            try:
                text = await asyncio.wait_for(
                    loop.run_in_executor(None, _call_gemini_sync, prompt, api_key),
                    timeout=GEMINI_TIMEOUT_SEC,
                )
                if text:
                    logger.info(f"Gemini success on attempt {attempt} (len={len(text)})")
                    return text
            except asyncio.TimeoutError:
                logger.warning(
                    f"Gemini attempt {attempt}/{GEMINI_MAX_TRIES}: timeout after {GEMINI_TIMEOUT_SEC}s",
                )
            except Exception as exc:
                logger.warning(f"Gemini attempt {attempt}/{GEMINI_MAX_TRIES}: error: {exc}")

        return None

        
    def _chunk_text(text: str, limit: int = SAFE_MSG_LIMIT) -> list[str]:
        if len(text) <= limit:
            return [text]

        seps = ["\n\n", "\n", " "]
        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= limit:
                chunks.append(remaining)
                break
            cut = -1
            for sep in seps:
                cut = remaining.rfind(sep, 0, limit)
                if cut > 0:
                    cut = cut + len(sep)
                    break
            if cut <= 0:
                cut = limit
            chunk = remaining[:cut].rstrip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[cut:].lstrip()

        return chunks

    async def _send_chunks(
        update: tg.Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        parse_mode: Optional[str],
        disable_web_page_preview: bool,
        ) -> None:
        
        chunks = _chunk_text(text, SAFE_MSG_LIMIT)
        logger.info(
            f"Telegram chunking: len={len(text)} chunks={len(chunks)} parse_mode={parse_mode}",
        )
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return

        failed_chunks: list[int] = []

        for i, chunk in enumerate(chunks):
            try:
                if i == 0 and update.message is not None:
                    await update.message.reply_text(
                        chunk,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                        do_quote=True
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                    )
            except Exception as chunk_exc:
                logger.warning(
                    f"Chunk {i + 1}/{len(chunks)} failed to send: {chunk_exc} — continuing best-effort delivery"
                )
                failed_chunks.append(i + 1)

            if len(chunks) > 1:
                await asyncio.sleep(0.5)

        if failed_chunks and chat_id is not None:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ Part of the output failed to send "
                        f"(chunk(s) {failed_chunks} of {len(chunks)}) — "
                        "please use /rawsignals for full data."
                    ),
                    parse_mode=None,
                    disable_web_page_preview=True,
                )
            except Exception:
                logger.exception("Failed to send failed chunks notification")

    async def _safe_reply(
        update: tg.Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = True,
    ) -> None:
        """Send with guaranteed delivery and never-raise guarantee."""
        if update.message is None:
            return

        if len(text) > SAFE_MSG_LIMIT:
            logger.info(
                f"Proactive chunking triggered: len={len(text)} > SAFE_MSG_LIMIT={SAFE_MSG_LIMIT}"
            )
            try:
                await _send_chunks(update, context, text,
                                parse_mode=parse_mode,
                                disable_web_page_preview=disable_web_page_preview)
                return
            except Exception as e_chunk:
                logger.warning(f"Proactive chunked send failed; attempting tosend again: {e_chunk}")
                try:
                    await _send_chunks(update, context, text,
                                    parse_mode=None,
                                    disable_web_page_preview=disable_web_page_preview)
                    return
                except Exception as e_plain:
                    logger.exception(f"Plain text chunked send also failed: {e_plain}")
                    try:
                        await update.message.reply_text(
                            text= f"Output was too large to deliver completely",
                            parse_mode=None,
                            disable_web_page_preview=True,
                            do_quote=True
                        )
                    except Exception:
                        pass
                    return

        try:
            await update.message.reply_text(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                do_quote=True
            )
            return
        except tg.error.TelegramError as e:
            err = str(e)
            print(f'Message Error: {err}')
            logger.warning(f"Telegram send failed; recovering. err={err}")

            if "Message is too long" in err:
                try:
                    await _send_chunks(update, context, text,
                                    parse_mode=parse_mode,
                                    disable_web_page_preview=disable_web_page_preview)
                    return
                except tg.error.TelegramError as e2:
                    logger.warning(f"Chunked send failed; plain text fallback. err={e2}")

            try:
                await _send_chunks(update, context, text,
                                parse_mode=None,
                                disable_web_page_preview=disable_web_page_preview)
            except Exception as e3:
                logger.exception(f"Telegram recovery failed: {e3}")
                if update.message is not None:
                    await update.message.reply_text(
                        "Output was too large to deliver completely. Please use /rawsignals.",
                        parse_mode=None,
                        disable_web_page_preview=True,
                    )
        
    if gemini_key:
        try:
            result = await _call_gemini(prompt, gemini_key)
        except Exception as exc:
            logger.warning(f"Gemini raised error: {exc}")
            await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('😢')])
            await update.message.reply_text(text=f"AI model raised error: {exc}\nPlease try the prompt again.", do_quote= True)
            result = None
        if result is not None:
            await _safe_reply(update, context, result, parse_mode=None, disable_web_page_preview=False)
        
    return RESPONSE
    
async def end_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nEnd Chat Triggered by user.")
    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👍')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    
    try:
        await update.effective_message.reply_text(
            text= f"AI chat session successfully ended.\n\nBye. I hope we can talk again!",
            do_quote=True,
        )
        print("AI Chat session Ended")
    except tg.error.NetworkError as error:
        print(f"Message Error: {error}")
        await update.effective_message.reply_text(
            text= f"Failed to end chat session, Try again: /end_chat",
            do_quote=True,
        )
    return ConversationHandler.END
    
# Main function to run the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, any_message)
    aichat_handler = CommandHandler('ai_chat', ai_chat)
    endchat_handler = CommandHandler('end_chat', end_chat)
    userid_handler = CommandHandler('id', user_id)
    help_handler = CommandHandler('help', help)
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
    
    # AI Chat Handler
    aichat_handler =ConversationHandler(
        entry_points= [CommandHandler("ai_chat", ai_chat)],
        states= {
            RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, response)]
        },
        fallbacks= [CommandHandler("end_chat", end_chat) ]
    )

    app.add_handler(conversation_handler)
    app.add_handler(aichat_handler)
    app.add_handler(endchat_handler)
    app.add_handler(start_handler)
    app.add_handler(message_handler)
    app.add_handler(userid_handler)
    app.add_handler(help_handler)
    
    app.add_handler(unknown_handler)

    try:
        app.run_polling(timeout= datetime.timedelta(seconds=15), bootstrap_retries= 3)
    except tg.error.TimedOut as error:
        print(f"Start-Up error: {error}")
    except tg.error.NetworkError as net_error:
        print(f"Network Error: {net_error}")


if __name__ == '__main__':
    main()
    
# effective_chat
# effective_user
# effective_sender
# effective_message