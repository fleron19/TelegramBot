import asyncio
import logging
import sqlite3
from telegram.ext import Application, MessageHandler, filters, CommandHandler
import telegram
from config import BOT_TOKEN

bot = telegram.Bot(BOT_TOKEN)
'''
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
'''


async def reg(update, context):
    con = sqlite3.connect('Replaces.db')
    user_id = str(update.message.from_user.id)
    code = str(context.args[0])
    print(code)
    print(user_id)
    codes = con.cursor().execute("""Select code from User""", ()).fetchall()
    if (code,) not in codes:
        await update.message.reply_text('Ошибка! Неверный код!')
    else:
        id = con.cursor().execute("""Select telId from User WHERE code = ?""", (code,)).fetchone()
        if id == (None,):
            con.cursor().execute("""Update User set telId = ? WHERE code = ?""", (user_id, code))
            con.commit()
            await update.message.reply_text('Регистрация прошла успешно!')
        else:
            await update.message.reply_text('Ошибка! Пользователь уже зарегестрирован!')



async def send(chat, msg):
    global application
    await application.bot.send_message(chat_id=chat, text=msg)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("reg", reg))
    application.run_polling()
    asyncio.run(send(1156166555, 'Hello there!'))


if __name__ == '__main__':
    main()
