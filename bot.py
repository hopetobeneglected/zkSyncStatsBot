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

file = open('data.json')
data = json.load(file)

TOKEN = data.get('token')
user_addresses = {}
logger.add('logs/bot.log', level='DEBUG', retention="1 day")

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
    logger.info(f"User {user.id} (username - {user.name}) clicked {update.message.text}")
    await update.message.reply_text(
        f"Sources:\n\n"
        f"zkFlow - `https://byfishh.github.io/zk-flow/`\n"
        f"zkSync explorer - `https://explorer.zksync.io/`\n\n"
        "Support - @Unexpectablee",
        parse_mode=ParseMode.MARKDOWN
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"User {user.id} (username - {user.name}) clicked {update.message.text}")
    await update.message.reply_text("Please send the addresses of your accounts line by line.\n"
                                    "_This bot can process max. 15 wallets at once due to telegram restrictions!_\n\n"
                                    "*Do not send private keys!*",
                                    parse_mode=ParseMode.MARKDOWN)
    return WALLETS


async def proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    user = update.message.from_user

    wallet_addresses = [line.strip() for line in message.strip().split("\n")]
    logger.info(f"User {user.id} (username - {user.name}) wrote {wallet_addresses}")

    sec = len(wallet_addresses)
    await update.message.reply_text("_Please wait... Estimated waiting time - 20 seconds_", parse_mode=ParseMode.MARKDOWN)
    result = checker.get_info(wallet_addresses)
    await update.message.reply_text(result[0])
    await update.message.reply_text(f"*{sec} wallet(s) were successfully proceeded!*\n\n"
                                    f"_Time required: {result[1]} seconds_", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    logger.info(f"Running your application")

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

    logger.success(f"Bot is running")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
