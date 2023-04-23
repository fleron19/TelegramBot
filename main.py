import asyncio
import logging
import sqlite3
from sqlite3 import Connection

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, PollAnswerHandler
import telegram
from config import BOT_TOKEN, DBNAME, TOTAL_VOTER_COUNT, HELP_DICT_T, HELP_DICT_ST, HELP_DICT_NOREG
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
    user_id = str(update.message.from_user.id)
    code = str(context.args[0])
    if code == '1h832f1':
        await update.message.reply_text('Зачем ты регестрируешь код из help? :P')
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


async def mes_cl(update, context):
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


async def mes_gr(update, context):
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
        group = context.args[0]
        message = str(context.args[1])
        if message:
            try:
                names = \
                    con.cursor().execute("""Select participants from Groups where name= ? """, (group,)).fetchone()[0]
            except:
                names = \
                    con.cursor().execute("""Select participants from Groups where shortName = ? """,
                                         (group,)).fetchone()[0]
                names = names.split(',')
            for i in names:
                anusers.append(
                    con.cursor().execute("""Select telId from User where name = ? """, (i,)).fetchone()[0]
                )
            print(anusers)
            if anusers:
                for i in anusers:
                    if str(i) != str(user_id):
                        loop.create_task(
                            (send(int(i), str('Тебе пришло сообщение от ' + user_name + ': ' + message))))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Некорректная или пустая группа!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Пустое сообщение!')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def mes_st(update, context):
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


async def mes_t(update, context):
    loop = asyncio.get_event_loop()
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con: Connection = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    name = context.args[0]
    teacherst = con.cursor().execute("""Select name from User where status = ? """, ('учитель',)).fetchall()
    teachers = []
    for i in teacherst:
        teachers.append(list(i)[0])
    if name in teachers:
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        blacklisted = con.cursor().execute("""Select studentName from Blacklist WHERE teacherName = ?""",
                                           (name,)).fetchall()
        print(blacklisted)
        blacklisted = list(blacklisted[0])[0].split(',')
        print(blacklisted)
        if user_name not in blacklisted:
            message = str(context.args[1])
            if message:
                i = con.cursor().execute("""Select telId from User where name = ? """, (name.strip(),)).fetchone()[0]
                loop.create_task(
                    (send(int(i), str('Вам пришло сообщение от ' + user_name + ': ' + message))))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Пустое сообщение!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Вы в черном списке у учителя!')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Учителя с таким именем нет!')


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
            for key in HELP_DICT_ST:
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
        else:
            try:
                for i in HELP_DICT_NOREG[command]:
                    await update.message.reply_text(i)
            except:
                await update.message.reply_text('Такой команды нет!')


async def add_gr(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    if status == ('учитель',):
        shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
        print(shortNames)
        if context.args[1] in shortNames[0]:
            participants = con.cursor().execute("""Select participants from Groups WHERE shortName = ?""",
                                                (context.args[1],)).fetchone()
            participants = participants[0]
            if participants is None:
                participants = context.args[0]
                con.cursor().execute("""Update Groups set participants = ? WHERE shortName = ?""",
                                     (participants, context.args[1]))
                con.commit()
            elif context.args[0] not in participants.split(','):
                participants = participants + ',' + context.args[0]
                con.cursor().execute("""Update Groups set participants = ? WHERE shortName = ?""",
                                     (participants, context.args[1]))
                con.commit()
                gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                          (context.args[1],)).fetchone()
                await update.message.reply_text(
                    'Пользователь ' + context.args[0] + ' успешно добавлен в группу ' + str(gr[0]))
                telId = con.cursor().execute("""Select telId from User WHERE name = ?""", (context.args[0],)).fetchone()
                group = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                             (context.args[1],)).fetchone()
                if telId:
                    loop.create_task(
                        send(telId[0], str('Вас добавили в группу ' + group[0])))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Пользователь ' + context.args[0] + ' уже находится в этой группе')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Группы с таким сокращением не существует')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def del_gr(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    if status == ('учитель',):
        shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
        print(shortNames)
        if context.args[1] in shortNames[0]:
            participants = con.cursor().execute("""Select participants from Groups WHERE shortName = ?""",
                                                (context.args[1],)).fetchone()
            participants = participants[0]
            if participants is None:
                participants = ''
            if context.args[0] in participants.split(','):
                participants = participants.split(',')
                participants.remove(context.args[0])
                participants = ','.join(participants)
                con.cursor().execute("""Update Groups set participants = ? WHERE shortName = ?""",
                                     (participants, context.args[1]))
                con.commit()
                gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                          (context.args[1],)).fetchone()
                await update.message.reply_text(
                    'Пользователь ' + context.args[0] + ' успешно удален из группы ' + str(gr[0]))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Пользователь ' + context.args[0] + ' не состоит в этой группе')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Группы с таким сокращением не существует')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def delete_gr(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(status)
    anusers = []
    if status == ('учитель',):
        shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
        if context.args[0] in shortNames[0]:
            gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""", (context.args[0],)).fetchone()
            con.cursor().execute("""DELETE from Groups WHERE shortName = ?""", (context.args[0],))
            con.commit()
            await update.message.reply_text('Группа ' + str(gr[0]) + ' успешно удалена')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Группы с таким сокращением не существует')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def create_gr(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    print(45)
    anusers = []
    if status == ('учитель',):
        names = con.cursor().execute("""Select name From Groups""").fetchall()
        if len(context.args) == 2:
            if context.args[0] not in names:
                shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
                if context.args[1] not in shortNames:
                    con.cursor().execute(
                        """INSERT INTO Groups (name, shortName)
                         values(?, ?)""",
                        (context.args[0], context.args[1]))
                    con.commit()
                    await update.message.reply_text('Группа добавлена успешно!')
                else:
                    await update.message.reply_text('Ошибка!')
                    await update.message.reply_text('Такое сокращение уже существует!')
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Такая группа уже существует!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text(
                'Неверное количество аргументов! Вы можете посмотреть функцию: /help create_gr')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def start(update, context):
    await update.message.reply_text('SchoolBot v 1.0')
    await update.message.reply_text('Бот для удобного взаимодействия учителей и учеников в школе')
    await update.message.reply_text('Введите /help для помощи по командам')


async def add_bl(update, context):
    context.args = ' '.join(update.message.text.split()[1:]).split('/')
    con = sqlite3.connect(DBNAME)
    name = context.args[0]
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    userst = con.cursor().execute("""Select name from User where status = ? """, ('ученик',)).fetchall()
    users = []
    for i in userst:
        users.append(list(i)[0])
    print(users)
    tname = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
    if status == ('учитель',):
        blacklisted = con.cursor().execute("""Select studentName from Blacklist WHERE teacherName = ?""",
                                           (tname,)).fetchall()
        print(blacklisted)
        if name in users:
            if not blacklisted:
                blacklisted = name
                con.cursor().execute("""insert into Blacklist (studentName, teacherName) values(?, ?)""",
                                     (blacklisted, tname))
                con.commit()
                await update.message.reply_text(
                    'Пользователь ' + name + ' успешно добавлен в черный список')
            else:
                blacklisted = list(blacklisted[0])[0].split(',')
                if name not in blacklisted:
                    blacklisted.append(name)
                    blacklisted = ','.join(blacklisted)
                    con.cursor().execute("""Update Blacklist set studentName = ? WHERE teacherName = ?""",
                                         (blacklisted, tname))
                    con.commit()
                    await update.message.reply_text(
                        'Пользователь ' + name + ' успешно добавлен в черный список')
                else:
                    await update.message.reply_text('Ошибка!')
                    await update.message.reply_text('Пользователь уже в черном списке!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Такого пользователя нет или он не ученик!')

    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


async def del_bl(update, context):
    name = context.args[0]
    loop = asyncio.get_event_loop()
    con = sqlite3.connect(DBNAME)
    user_id = str(update.message.from_user.id)
    status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
    tname = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
    print(status)
    if status == ('учитель',):
        blacklisted = con.cursor().execute("""Select studentName From Blacklist where teacherName = ?""", (tname,)).fetchall()
        blacklisted = list(blacklisted[0])[0].split(',')
        if name in blacklisted:
            blacklisted.remove(name)
            blacklisted = ','.join(blacklisted)
            con.cursor().execute("""Update Blacklist set studentName = ? WHERE teacherName = ?""",
                                 (blacklisted, tname))
            con.commit()
            blacklisted = con.cursor().execute("""Select studentName From Blacklist where teacherName = ?""",
                                               (tname,)).fetchall()
            blacklisted = list(blacklisted[0])[0].split(',')
            print(blacklisted)
            if blacklisted == ['']:
                con.cursor().execute("""Delete From Blacklist where teacherName = ?""",
                                                   (tname,)).fetchall()
                con.commit()

            await update.message.reply_text(
                'Пользователь ' + name + ' успешно удален из черного списка')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Такого пользователя нет в черном списке!')
    else:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('У вас нет прав на использование этой команды!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reg", reg))
    application.add_handler(CommandHandler("les", les))
    application.add_handler(CommandHandler("mes_cl", mes_cl))
    application.add_handler(CommandHandler("mes_st", mes_st))
    application.add_handler(CommandHandler("mes_t", mes_t))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("add_rep", add_rep))
    application.add_handler(CommandHandler("remove_rep", remove_rep))
    application.add_handler(CommandHandler("poll_ans", poll_ans))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_handler(CommandHandler("ans_table", ans_table))
    application.add_handler(CommandHandler("new_user", new_user))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("create_gr", create_gr))
    application.add_handler(CommandHandler("add_gr", add_gr))
    application.add_handler(CommandHandler("del_gr", del_gr))
    application.add_handler(CommandHandler("delete_gr", delete_gr))
    application.add_handler(CommandHandler("mes_gr", mes_gr))
    application.add_handler(CommandHandler("add_bl", add_bl))
    application.add_handler(CommandHandler("del_bl", del_bl))
    application.run_polling()


if __name__ == '__main__':
    main()
