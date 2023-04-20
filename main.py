import asyncio
import logging
import sqlite3
from sqlite3 import Connection

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, PollAnswerHandler
import telegram
from config import BOT_TOKEN, DBNAME, TOTAL_VOTER_COUNT, HELP_DICT_T, HELP_DICT_ST
from datetime import *
from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
)
import xlsxwriter
from random import *

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
    '''
    print(type(td))
    td = datetime.strptime("2023-04-18", '%Y-%m-%d').date()
    print(td)
    '''
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
    if code == '1h832f1':
        await update.message.reply_text('Зачем ты регестрируешь код и help? :P')
    else:
        print(code)
        print(user_id)
        codes = con.cursor().execute("""Select code from User""", ()).fetchall()
        if (code,) not in codes:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Неверный код!')
        else:
            id = con.cursor().execute("""Select telId from User WHERE code = ?""", (code,)).fetchone()
            print(id)
            if id == (None,) or id == ('',):
                con.cursor().execute("""Update User set telId = ? WHERE code = ?""", (user_id, code))
                con.commit()
                name = con.cursor().execute("""SELECT name From User WHERE code = ?""", (code,)).fetchone()[0]
                status = con.cursor().execute("""SELECT status From User WHERE code = ?""", (code,)).fetchone()[0]
                print(name)
                if status == 'ученик':
                    resstr = 'Регистрация прошла успешно! Привет, ' + str(name) + '!'
                else:
                    resstr = 'Регистрация прошла успешно! Здравсивуйте, ' + str(status) + '!'
                await update.message.reply_text(resstr)
            else:
                await update.message.reply_text(resstr)


async def send(chat, msg):
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.send_message(chat_id=chat, text=msg)


async def sendDocument(chat, doc):
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.send_document(chat_id=chat, document=doc)


async def announce_cl(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    anusersnorm = []
    if status == ('учитель',):
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        cl = context.args[0].split(',')
        message = str(context.args[1])
        if message:
            for i in cl:
                print(i)
                anusers.append(con.cursor().execute("""Select telId from User where class = ? """,
                                                    (i.lower().strip(),)).fetchall())
            print(anusers)
            for i in anusers:
                for q in i:
                    anusersnorm.append(q)
            anusers = anusersnorm
            print(anusers)
            if anusers:
                for i in anusers:
                    if i != (None,) and i:
                        i = list(i)[0]
                        if str(i) != str(user_id):
                            loop.create_task(
                                (send(int(i), str('Тебе пришло сообщение от ' + user_name + ': ' + message))))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Некорректный или пустой класс!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Пустое сообщение!')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def announce_st(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    if status == ('учитель',):
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        names = context.args[0].split(',')
        print(names)
        message = str(context.args[1])
        if message:
            for i in names:
                print(i)
                anusers.append(
                    con.cursor().execute("""Select telId from User where name = ? """, (i.strip(),)).fetchone())
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
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Некорректное имя!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Пустое сообщение!')
    else:
        await update.message.reply_text('Ошибка!')
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
        z = con.cursor().execute(
            """SELECT * FROM Replace WHERE day = ? and classRep = ? and numLesson = ?""",
            (rep[0], rep[1], str(int(rep[2]) - 1))).fetchall()
        print(z)
        if not z:
            con.cursor().execute(
                """INSERT INTO Replace (day, classRep, lessonRep, numLesson, room, teacherId)
                 values(?, ?, ?, ?, ?, ?)""",
                (rep[0], rep[1], rep[3], str(int(rep[2]) - 1), rep[4], 1))
            con.commit()
            await update.message.reply_text('Замена добавлена')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Такая замена уже есть!')

    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


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
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def poll(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    questions = [context.args[2].split(', ')]
    questions = questions[0]
    print(questions)
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    anusersnorm = []
    if status == ('учитель',):
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        print(user_name)
        cl = context.args[0].split(', ')
        for i in cl:
            print(i)
            anusers.append(con.cursor().execute("""Select telId from User where class = ? """,
                                                (i.lower().strip(),)).fetchall())
        print(anusers)
        for i in anusers:
            for q in i:
                anusersnorm.append(q)
        anusers = anusersnorm
        print(anusers)
        typ = len(con.cursor().execute("""Select * from Survey """).fetchall()) + 1
        if anusers:
            for i in anusers:
                if i != (None,) and i and i != ('',):
                    print(i)
                    i = list(i)[0]
                    if str(i) != str(user_id):
                        print(i)
                        loop = asyncio.get_event_loop()
                        await loop.create_task(
                            (send(int(i), str('Тебе пришел опрос от ' + user_name))))
                        message = await context.bot.send_poll(
                            int(i),  # int(i)
                            context.args[1],
                            questions,
                            is_anonymous=False,
                            allows_multiple_answers=False,
                        )
                        # Save some info about the poll the bot_data for later use in receive_poll_answer
                        idpoll = message.message_id
                        payload = {
                            message.poll.id: {
                                "questions": questions,
                                "message_id": idpoll,
                                "chat_id": update.effective_chat.id,  # update.effective_chat.id
                                "answers": 0,
                            }
                        }
                        context.bot_data.update(payload)
                        con.cursor().execute(
                            """INSERT INTO Survey (id, text, classes, variants, typ, author)
                             values(?, ?, ?, ?, ?, ?)""",
                            (idpoll, context.args[1], context.args[0], ','.join(questions), typ, user_name))
                        con.commit()
            await update.message.reply_text('Опрос успешно создан! ID опроса: ' + str(idpoll))


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    idpoll = context.bot_data[answer.poll_id]['message_id']
    print(idpoll)
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    # await context.bot.send_message(
    # answered_poll["chat_id"],
    # f"{update.effective_user.mention_html()} feels {answer_string}!",
    # parse_mode=ParseMode.HTML,
    # )
    answered_poll["answers"] += 1
    # Close poll after three participants voted
    if answered_poll["answers"] == TOTAL_VOTER_COUNT:
        await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])
    con = sqlite3.connect(DBNAME)
    ans = con.cursor().execute("""Select answer From Survey where id = ?""", (idpoll,)).fetchone()
    print(ans)
    if ans == ('None',):
        user_name = \
            con.cursor().execute("""Select name from User where telId = ? """, (update.effective_user.id,)).fetchone()[
                0]
        ansnew = str(answer_string)
        print(user_name)
        con.cursor().execute("update Survey set name = ?, answer = ? WHERE id = ?", (user_name, ansnew, idpoll))
        con.commit()
    print(ans)
    print(update.effective_user.id)


async def ans_table(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    idpoll = context.args[0]
    print(idpoll)
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
    author = con.cursor().execute("""Select author From Survey where id = ?""", (idpoll,)).fetchone()[0]
    print(user_name, author)
    if user_name == author or 1 == 1:
        typ = con.cursor().execute("""Select typ From Survey where id = ?""", (str(idpoll),)).fetchall()
        print(typ)
        ans = []
        # for elem in ids:
        answer = con.cursor().execute("""Select name, answer From Survey where typ = ?""", (typ[0][0],)).fetchall()
        for elem in answer:
            if elem[0] != 'None':
                ans.append(elem)
        print(ans)
        if ans == 'None' or ans == None or ans == ('None',) or ans == []:
            await update.message.reply_text('Опрос ' + str(idpoll) + ' никто ещё не прошел!')
        else:
            print(ans)
            resstr = []
            ansres = []
            for elem in ans:
                data = [('Пользователь', 'Ответ')]
                for elem in ans:
                    data.append((elem[0], elem[1]))
        print(data)
        title = 'Ответы на опрос ' + idpoll + '.xlsx'
        workbook = xlsxwriter.Workbook(title)
        worksheet = workbook.add_worksheet()
        for row, (nameans, ans) in enumerate(data):
            worksheet.write(row, 0, nameans)
            worksheet.write(row, 1, ans)
        row += 1
        workbook.close()
        await sendDocument(user_id, title)


async def new_user(update, context):
    con = sqlite3.connect(DBNAME)
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    name = context.args[0]
    clas = context.args[1]
    stat = context.args[2]
    codes = con.cursor().execute("""Select code From User""").fetchall()
    print(codes)
    for elem in codes:
        elem = elem[0]
    code = -1
    while code in codes or code == -1:
        code = []
        for i in range(0, 3):
            code.append(chr(randrange(97, 123)))
        for i in range(0, 3):
            code.append(str(randrange(0, 10)))
        code = ''.join(code)
    con.cursor().execute(
        """INSERT INTO User (name, status, class, code)
         values(?, ?, ?, ?)""",
        (name, stat, clas, code))
    con.commit()
    await update.message.reply_text('Пользователь успешно добавлен! ' + name + " с кодом:" + code)


async def poll_ans(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    idpoll = context.args[0]
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
    author = con.cursor().execute("""Select author From Survey where id = ?""", (idpoll,)).fetchone()[0]
    if user_name == author:
        typ = con.cursor().execute("""Select typ From Survey where id = ?""", (idpoll,)).fetchall()
        print(typ)
        ans = []
        # for elem in ids:
        answer = con.cursor().execute("""Select name, answer From Survey where typ = ?""", (typ[0][0],)).fetchall()
        for elem in answer:
            if elem[0] != 'None':
                ans.append(elem)
        print(ans)
        if ans == 'None' or ans == None or ans == ('None',) or ans == []:
            await update.message.reply_text('Опрос ' + str(idpoll) + ' никто ещё не прошел!')
        else:
            print(ans)
            resstr = []
            ansres = []
            for elem in list(ans):
                elem = ' - '.join(elem)
                resstr.append(elem)
            resstr = '\n'.join(resstr)
            if resstr:
                await update.message.reply_text('Ответы на опрос ' + str(idpoll) + ':')
                await update.message.reply_text(resstr)
    else:
        await update.message.reply_text('Вы не являетесь автором опроса!')


async def help(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    print(context.args)
    if context.args == ['']:
        status = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()[0]
        if status == 'учитель':
            for key in HELP_DICT_T:
                await update.message.reply_text(HELP_DICT_T[key][0])
        elif status == 'ученик':
            for key in HELP_DICT_T:
                await update.message.reply_text(HELP_DICT_ST[key][0])
    else:
        command = context.args[0]
        status = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()[0]
        if status == 'учитель':
            try:
                for i in HELP_DICT_T[command]:
                    await update.message.reply_text(i)
            except:
                await update.message.reply_text('Такой команды нет!')
        elif status == 'ученик':
            try:
                for i in HELP_DICT_ST[command]:
                    await update.message.reply_text(i)
            except:
                await update.message.reply_text('Такой команды нет!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("reg", reg))
    application.add_handler(CommandHandler("les", les))
    application.add_handler(CommandHandler("announce_cl", announce_cl))
    application.add_handler(CommandHandler("announce_st", announce_st))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("add_rep", add_rep))
    application.add_handler(CommandHandler("remove_rep", remove_rep))
    application.add_handler(CommandHandler("poll_ans", poll_ans))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_handler(CommandHandler("ans_table", ans_table))
    application.add_handler(CommandHandler("new_user", new_user))
    application.add_handler(CommandHandler("help", help))
    application.run_polling()


if __name__ == '__main__':
    main()
