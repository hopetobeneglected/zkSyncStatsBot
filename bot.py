import asyncio
import json
from telegram.constants import ParseMode
import checker
from loguru import logger
from telegram import ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, ApplicationBuilder,
)
import aiohttp

async def handle(request):
    return aiohttp.web.Response(text="Hello from your bot's web server!")

file = open('data.json')
data = json.load(file)

TOKEN = data.get('token')
user_addresses = {}
# logger.add('/tmp/logs/bot.log', level='DEBUG', retention="1 day")

WALLETS, NEXT_STEP = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_buttons = [[KeyboardButton('Get statistic')], [KeyboardButton('Info')]]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Hi, {update.effective_user.name}!\n\n"
                                        "Click on the button below to get the "
                                        "statistic of your accounts!",
                                   reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True,
                                                                    one_time_keyboard=True))


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # logger.info(f"User {user.id} (username - {user.name}) clicked {update.message.text}")
    await update.message.reply_text(
        f"Sources:\n\n"
        f"zkFlow - `https://byfishh.github.io/zk-flow/`\n"
        f"zkSync explorer - `https://explorer.zksync.io/`\n\n"
        "Support - @Unexpectablee",
        parse_mode=ParseMode.MARKDOWN
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    # logger.info(f"User {user.id} (username - {user.name}) clicked {update.message.text}")
    await update.message.reply_text("_Please send me addresses of your accounts line by line_.\n\n"
                                    "*Do not send private keys!*",
                                    parse_mode=ParseMode.MARKDOWN)
    return WALLETS


async def proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Echo the user message."""
    message = update.message.text
    user = update.message.from_user

    wallet_addresses = [line.strip() for line in message.strip().split("\n")]
    # logger.info(f"User {user.id} (username - {user.name}) wrote {wallet_addresses}")

    sec = len(wallet_addresses) * 1
    message = update.message

    sent_message = await message.reply_text(
        f"_Please wait... Estimated waiting time - {sec} seconds_",
        parse_mode=ParseMode.MARKDOWN)

    async def send(seconds):
        for i in range(0, seconds):
            seconds -= 1
            await asyncio.sleep(1)
            await sent_message.edit_text(
                text=f"_Please wait... Estimated waiting time - {seconds} seconds_",
                parse_mode=ParseMode.MARKDOWN)

    result = checker.get_info(wallet_addresses)
    await update.message.reply_text(result)
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    info_handler = MessageHandler(filters.Regex("^Info$"), info)
    application.add_handler(info_handler)

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Get statistic$"), stats)],
        states={
            WALLETS: [MessageHandler(filters.Regex("^((0x[0-9a-fA-F]{40})\r?\n?)+$"), proceed)]
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Get statistic$"), stats),
            MessageHandler(filters.Regex("^Info$"), info),
            MessageHandler(~filters.Regex("^((0x[0-9a-fA-F]{40})\r?\n?)+$"), unknown)]
    )
    application.add_handler(conv_handler)

    unknown_handler = MessageHandler(filters.COMMAND | filters.TEXT, unknown)
    application.add_handler(unknown_handler)

    # application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    web_app = aiohttp.web.Application()
    web_app.router.add_get('/', handle)

    # Run both the polling and web server concurrently
    loop = asyncio.get_event_loop()
    tasks = [
        application.run_polling(allowed_updates=Update.ALL_TYPES),
        aiohttp.web.run_app(web_app, host='0.0.0.0', port=3000),
    ]
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    main()
