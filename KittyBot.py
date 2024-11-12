# main KittyBot.py
import time
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
import importlib
import cat20_telegram.KittyBot.bot_config.config
importlib.reload(cat20_telegram.KittyBot.bot_config.config)
from cat20_telegram.KittyBot.bot_config.config import (
    TELEGRAM_KITTYBOT_TOKEN, 
    INTERVAL_BUYBOT,
    INTERVAL_HOTMINT,
    FEATURES_ENABLED
)
from cat20_telegram.KittyBot.handlers.mint import monitor_tokens_wrapper
from cat20_telegram.KittyBot.handlers.buybot import (
    buybot_command,
    receive_token_id,
    receive_media,
    receive_emoji,
    receive_x_link,
    receive_telegram_link,
    receive_website_link,
    receive_threshold,
    skip_media_upload,
    skip_emoji,
    skip_x_link,
    skip_telegram_link,
    skip_website_link,
    stop_buybot_callback,
    monitor_all_buybots,
    stop_buybot_command,
    list_buybots_command
)
from cat20_telegram.KittyBot.state import (
    BUYBOT_WAITING_FOR_TOKEN_ID,
    BUYBOT_WAITING_FOR_MEDIA,
    BUYBOT_WAITING_FOR_EMOJI,
    BUYBOT_WAITING_FOR_X_LINK,
    BUYBOT_WAITING_FOR_TELEGRAM_LINK,
    BUYBOT_WAITING_FOR_WEBSITE_LINK,
    TOKEN_WAITING_FOR_TOKEN_ID,
    BALANCE_WAITING_FOR_ADDRESS,
    BUYBOT_WAITING_FOR_THRESHOLD
)
from cat20_telegram.KittyBot.handlers.token_info import receive_token_info_id, cancel_token
from cat20_telegram.KittyBot.handlers.balance import receive_balance_address, cancel_balance
from cat20_telegram.KittyBot.utils.json_handler import (
    load_hot_mint_preferences, 
    load_buybot_preferences, 
    save_buybot_preferences, 
    load_preferences,
    load_rate_limit_metadata,
    load_fb_price
)

# Import handler functions
from cat20_telegram.KittyBot.handlers.start import (
    start,
    start_handler, 
    set_language
)   
from cat20_telegram.KittyBot.utils.buttons import (
    buybot_button, 
    hotmint_button, 
    start_balance_button, 
    start_token_button, 
    change_language_button,
    help_button,
    fees_button,
    stop_hotmint_button
)
from cat20_telegram.KittyBot.handlers.help import help_command
from cat20_telegram.KittyBot.handlers.fees import current_mempool_fees
from cat20_telegram.KittyBot.handlers.balance import balance_command
from cat20_telegram.KittyBot.handlers.health import health_command
from cat20_telegram.KittyBot.handlers.mint import restricted_hotmint_command, restricted_stop_hotmint_command
from cat20_telegram.KittyBot.handlers.token_info import token_info_command
from cat20_telegram.KittyBot.handlers.cancel_handler import cancel_command
#from cat20_telegram.KittyBot.handlers.ask import ask_command
from cat20_telegram.KittyBot.handlers.message import handle_message
from cat20_telegram.KittyBot.utils.bot_name import set_bot_username
from cat20_telegram.KittyBot.utils.message_manager import MessageManager

from cat20_telegram.KittyBot.logger_config import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cat20_telegram.KittyBot.handlers.fb_price import fetch_and_save_fb_price

from zoneinfo import ZoneInfo

def main():
    # Create the application
    application = ApplicationBuilder().token(TELEGRAM_KITTYBOT_TOKEN).build()

    # Initialize MessageManager and store in bot_data
    application.bot_data['message_manager'] = MessageManager()

    # Load user language preferences and hot_mint_preferences
    application.bot_data['user_language_preferences'] = load_preferences()
    application.bot_data['hot_mint_preferences'] = load_hot_mint_preferences()
    application.bot_data['buybot_preferences'] = load_buybot_preferences()
    application.bot_data['rate_limit_metadata'] = load_rate_limit_metadata()

    application.bot_data['buybot_active'] = False

    application.bot_data['fb_price_data'] = load_fb_price()

    # Initialize and start the scheduler
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Berlin"))
    scheduler.add_job(fetch_and_save_fb_price, 'interval', hours=1, args=[application.bot_data])

    # Fetch FB price immediately at startup
    fetch_and_save_fb_price(application.bot_data)
    # Schedule the bot username retrieval
    application.job_queue.run_once(lambda context: asyncio.create_task(set_bot_username(application)), 0)

    # Add command handlers for group and private chats
    if FEATURES_ENABLED.get('core', False):
        application.add_handler(CommandHandler('kittystart', start))
        # application.add_handler(CommandHandler('start', start_handler))
        application.add_handler(CommandHandler('kittyhealth', health_command))

        application.add_handler(CommandHandler('kittyhelp', help_command))
        application.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))

        application.add_handler(CommandHandler('kittyfees', current_mempool_fees))
        application.add_handler(CallbackQueryHandler(fees_button, pattern="^fees$"))

        application.add_handler(CallbackQueryHandler(change_language_button, pattern="^change_language$"))
        application.add_handler(CallbackQueryHandler(set_language, pattern="^set_language_"))

    if FEATURES_ENABLED.get('token_info', False):
        #application.add_handler(CommandHandler('token', start_token_conversation))
    
        # Add ConversationHandlers for /token
        token_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('kittytoken', token_info_command),
                CallbackQueryHandler(start_token_button, pattern="^start_token$")
            ],
            states={
                TOKEN_WAITING_FOR_TOKEN_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token_info_id)
                ]
            },
            fallbacks=[
                CommandHandler("kittycancel", cancel_token), 
                ],
            per_chat=True,
            per_user=True
        )
        application.add_handler(token_conv_handler)

    if FEATURES_ENABLED.get('balance', False):
        #application.add_handler(CommandHandler('balance', start_balance_conversation))

        # Add ConversationHandlers for /balance
        balance_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('kittybalance', balance_command),
                CallbackQueryHandler(start_balance_button, pattern="^start_balance$")
            ],
            states={
                BALANCE_WAITING_FOR_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_balance_address)
                ]
            },
            fallbacks=[
                CommandHandler("kittycancel", cancel_balance), 
                ],
            per_chat=True,
            per_user=True
        )
        application.add_handler(balance_conv_handler)

    if FEATURES_ENABLED.get('hotmint', False):
    
        #application.add_handler(CommandHandler('mint_progress', mint_progress_command))
        application.add_handler(CommandHandler("kittyhotmint", restricted_hotmint_command))
        application.add_handler(CommandHandler("kittyhotmintstop", restricted_stop_hotmint_command))
        application.add_handler(CallbackQueryHandler(hotmint_button, pattern="^start_hotmint$"))
        #application.add_handler(CallbackQueryHandler(stop_hotmint_button, pattern="^stop_hotmint$"))

        # Load hot mint preferences
        hot_mint_preferences = application.bot_data['hot_mint_preferences']
        # For each chat with active hot mint monitoring
        for chat_id, prefs in hot_mint_preferences.items():
            if prefs.get('active', False):
                # Get the interval; use default if not specified
                interval = prefs.get('interval', INTERVAL_HOTMINT)
                min_threshold = prefs.get('min_threshold', 80)
                max_threshold = prefs.get('max_threshold', 95)
                premine_threshold = prefs.get('premine_threshold', 0)
                # Schedule the monitor_tokens_wrapper function
                application.job_queue.run_repeating(
                    monitor_tokens_wrapper,
                    interval=interval,
                    first=0,
                    name=f"hotmint_{chat_id}",
                    data={
                        'chat_id': chat_id,
                        'min_threshold': min_threshold,
                        'max_threshold': max_threshold,
                        'premine_threshold': premine_threshold
                    }
                )
                logger.info(f"Scheduled hot mint monitoring for chat_id: {chat_id} with interval: {interval}")
        

    if FEATURES_ENABLED.get('buybot', False):
        # Add CallbackQueryHandler for stopping buybot
        application.add_handler(CallbackQueryHandler(stop_buybot_callback, pattern="^sb_stop_"), group=0)
        # Add CallbackQueryHandler for starting buybot setup
        #application.add_handler(CallbackQueryHandler(buybot_button, pattern="^start_buybot_setup$"), group=0)
        application.add_handler(CallbackQueryHandler(buybot_button, pattern="^start_buybot$"), group=0)

        # Schedule the Buybot monitoring job to run at intervals defined by INTERVAL_BUYBOT
        scheduler.add_job(
            monitor_all_buybots,
            'interval',
            seconds=INTERVAL_BUYBOT,
            args=[application],
            name='Monitor_All_Buybots'
        )
        # Define ConversationHandlers for Buybot

        # 1. Group Chat Buybot ConversationHandler
        buybot_group_conversation = ConversationHandler(
            entry_points=[
                CommandHandler("kittybuybot", buybot_command)
            ],
            states={
                BUYBOT_WAITING_FOR_TOKEN_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token_id)
                ],
                BUYBOT_WAITING_FOR_THRESHOLD: [  
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_threshold)
                ],
                BUYBOT_WAITING_FOR_MEDIA: [
                    MessageHandler(filters.ALL & ~filters.COMMAND, receive_media),
                    CommandHandler("kittyskip", skip_media_upload)
                ],
                BUYBOT_WAITING_FOR_EMOJI: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_emoji),
                    CommandHandler('kittyskip', skip_emoji)
                ],
                BUYBOT_WAITING_FOR_X_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_x_link),
                    CommandHandler('kittyskip', skip_x_link)
                ],
                BUYBOT_WAITING_FOR_TELEGRAM_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_telegram_link),
                    CommandHandler('kittyskip', skip_telegram_link)
                ],
                BUYBOT_WAITING_FOR_WEBSITE_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_website_link),
                    CommandHandler('kittyskip', skip_website_link)
                ],
            },
            fallbacks=[
                CommandHandler("kittycancel", cancel_command)
            ],
            per_chat=True,
            per_user=True
        )
        application.add_handler(buybot_group_conversation, group=0)

        # 2. Private Chat Buybot Setup ConversationHandler
        buybot_private_conversation = ConversationHandler(
            entry_points=[
                #CommandHandler("kittybuybot", buybot_command),
                #CallbackQueryHandler(buybot_button, pattern="^start_buybot$"),
                CommandHandler("start", start_handler)
            ],
            states={
                BUYBOT_WAITING_FOR_TOKEN_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token_id)
                ],
                BUYBOT_WAITING_FOR_THRESHOLD: [  
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_threshold)
                ],
                BUYBOT_WAITING_FOR_MEDIA: [
                    MessageHandler(filters.ALL & ~filters.COMMAND, receive_media),
                    CommandHandler("kittyskip", skip_media_upload)
                ],
                BUYBOT_WAITING_FOR_EMOJI: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_emoji),
                    CommandHandler('kittyskip', skip_emoji)
                ],
                BUYBOT_WAITING_FOR_X_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_x_link),
                    CommandHandler('kittyskip', skip_x_link)
                ],
                BUYBOT_WAITING_FOR_TELEGRAM_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_telegram_link),
                    CommandHandler('kittyskip', skip_telegram_link)
                ],
                BUYBOT_WAITING_FOR_WEBSITE_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_website_link),
                    CommandHandler('kittyskip', skip_website_link)
                ],
            },
            fallbacks=[
                CommandHandler("kittycancel", cancel_command)
            ],
            per_chat=True,
            per_user=True
        )
        application.add_handler(buybot_private_conversation, group=0)

        application.add_handler(CommandHandler("kittybuybotstop", stop_buybot_command), group=0)
        application.add_handler(CommandHandler("kittylistbuybots", list_buybots_command), group=0)

    # Add handlers for cancel button and command
    if FEATURES_ENABLED.get('cancel', False):
        cancel_handler = CommandHandler("kittycancel", cancel_command)
        cancel_button_handler = CallbackQueryHandler(cancel_command, pattern='^cancel_command$')
        application.add_handler(cancel_handler)
        application.add_handler(cancel_button_handler)

    if FEATURES_ENABLED.get('ai', False):
        # Add the AI MessageHandler with lower priority (group 1)
        message_filter = filters.TEXT & ~filters.COMMAND
        message_handler = MessageHandler(message_filter, handle_message)
        application.add_handler(
            message_handler,
            group=1  # Lower priority than ConversationHandlers
        )

    # Start the scheduler
    scheduler.start()

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
