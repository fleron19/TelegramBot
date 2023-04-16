import asyncio
import logging
import sqlite3
from sqlite3 import Connection

from telegram.ext import Application, MessageHandler, filters, CommandHandler
import telegram
from config import BOT_TOKEN, DBNAME
from datetime import *

bot = telegram.Bot(BOT_TOKEN)
'''
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
'''


async def les(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con = sqlite3.connect(DBNAME)
    td = date.today()
    print(type(td))
    td = datetime.strptime("2023-04-18", '%Y-%m-%d').date()
    print(td)
    user_id = str(update.message.from_user.id)
    clas = con.cursor().execute("""Select class From User where telid = ?""", (user_id,)).fetchall()
    rep = con.cursor().execute("""Select numLesson, lessonRep, room From Replace where classRep = ? and day = ?""",
                               (clas[0][0], str(td),)).fetchall()
    tdweek = td.weekday()
    print(tdweek)
    lessons = con.cursor().execute(
        """Select lesson, room From Schedule where class = ? and dayOfWeek = ? order by numLesson""",
        (clas[0][0], tdweek + 1,)).fetchall()
    schedule = []
    for elem in lessons:
        schedule.append(str(elem[0]) + ' ' + str(elem[1]))
    for elem in rep:
        schedule[elem[0]] = "Замена: " + str(elem[1]) + ' ' + str(elem[2])
    resstr = "\n".join(schedule)
    if resstr:
        await update.message.reply_text('У Вас сегодня:')
        await update.message.reply_text(resstr)
    else:
        await update.message.reply_text('Сегодня у вас нет уроков!')


async def reg(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con = sqlite3.connect(DBNAME)
    context.args = context.args.split('/')
    user_id = str(update.message.from_user.id)
    code = str(context.args[0])
    print(code)
    print(user_id)
    codes = con.cursor().execute("""Select code from User""", ()).fetchall()
    if (code,) not in codes:
        await update.message.reply_text('Ошибка! Неверный код!')
    else:
        id = con.cursor().execute("""Select telId from User WHERE code = ?""", (code,)).fetchone()
        print(id)
        if id == (None,) or id == ('',):
            con.cursor().execute("""Update User set telId = ? WHERE code = ?""", (user_id, code))
            con.commit()
            name = con.cursor().execute("""SELECT name From User WHERE code = ?""", (code,)).fetchone()
            print(name)
            resstr = 'Регистрация прошла успешно! Привет, ' + str(name[0]) + '!'
            await update.message.reply_text(resstr)
        else:
            await update.message.reply_text(resstr)


async def send(chat, msg):
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.send_message(chat_id=chat, text=msg)


async def announce_cl(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    if status == ('учитель',):
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        cl = str(context.args[0].lower())
        message = str(context.args[1])
        if message:
            anusers = con.cursor().execute("""Select telId from User where class = ? """, (cl,)).fetchall()
            print(anusers)
            if anusers:
                for i in anusers:
                    if i != (None,) and i:
                        i = list(i)[0]
                        if str(i) != str(user_id):
                            loop.create_task(
                                (send(int(i), str('Тебе пришло сообщение от ' + user_name + ': ' + message))))
            else:
                await update.message.reply_text('Некорректный или пустой класс!')
        else:
            await update.message.reply_text('Пустое сообщение!')
    else:
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def announce_st(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    if status == ('учитель',):
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        name = str(context.args[0])
        message = str(context.args[1])
        if message:
            anusers = con.cursor().execute("""Select telId from User where name = ? """, (name,)).fetchall()
            print(anusers)
            if anusers:
                for i in anusers:
                    if i != (None,) and i:
                        i = list(i)[0]
                        if str(i) != str(user_id):
                            print('sent')
                            loop.create_task(
                                (send(int(i), str('Тебе пришло сообщение от ' + user_name + ': ' + message))))
            else:
                await update.message.reply_text('Некорректное имя!')
        else:
            await update.message.reply_text('Пустое сообщение!')
    else:
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def add_rep(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con: Connection = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    stat = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()
    print(context.args)
    if stat == ('учитель',):
        rep = context.args
        rep[0] = "2023-" + rep[0]
        con.cursor().execute(
            """INSERT INTO Replace (day, classRep, lessonRep, numLesson, room, teacherId) values(?, ?, ?, ?, ?, ?)""",
            (rep[0], rep[1], rep[3], str(int(rep[2]) - 1), rep[4], 1))
        con.commit()


async def remove_rep(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con: Connection = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    stat = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()
    print(context.args)
    if stat == ('учитель',):
        rep = context.args
        rep[0] = "2023-" + rep[0]
        print((rep[0], rep[1], str(rep[2])))
        con.cursor().execute(
            """DELETE FROM Replace WHERE day = ? and classRep = ? and numLesson = ? """,
            (rep[0], rep[1], str(int(rep[2]) - 1)))
        con.commit()
        await update.message.reply_text('Замена успешно удалена!')
    else:
        await update.message.reply_text('У вас нет прав на использование этой команды!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("reg", reg))
    application.add_handler(CommandHandler("les", les))
    application.add_handler(CommandHandler("announce_cl", announce_cl))
    application.add_handler(CommandHandler("announce_st", announce_st))
    application.add_handler(CommandHandler("add_rep", add_rep))
    application.add_handler(CommandHandler("remove_rep", remove_rep))
    application.run_polling()
    asyncio.run(send(1156166555, 'Hello there!'))


if __name__ == '__main__':
    main()
