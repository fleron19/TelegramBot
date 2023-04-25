# import необходимых библиотек
import asyncio
import sqlite3
import logging
from sqlite3 import Connection

import telegram
from datetime import *
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PollAnswerHandler,
)
import xlsxwriter
import requests
# import констант из файла config.py
from config import BOT_TOKEN, DBNAME, TOTAL_VOTER_COUNT, HELP_DICT_T, HELP_DICT_ST, HELP_DICT_NOREG

bot = telegram.Bot(BOT_TOKEN)

# включение logging а
'''
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
'''


# /les - команда для вывода уроков
async def les(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con = sqlite3.connect(DBNAME)
        td = date.today()
        td = td + timedelta(days=int(context.args[0]))
        '''
        print(type(td))
        td = datetime.strptime("2023-04-18", '%Y-%m-%d').date()
        print(td)
        '''
        # получение id пользователя, класса где он учится и его замен
        user_id = str(update.message.from_user.id)
        clas = con.cursor().execute("""Select class From User where telid = ?""", (user_id,)).fetchall()
        rep = con.cursor().execute("""Select numLesson, lessonRep, room From Replace where classRep = ? and day = ?""",
                                   (clas[0][0], str(td),)).fetchall()
        tdweek = td.weekday()
        print(tdweek)
        # получение сегоднящних уроков у ученика
        lessons = con.cursor().execute(
            """Select lesson, room From Schedule where class = ? and dayOfWeek = ? order by numLesson""",
            (clas[0][0], tdweek + 1,)).fetchall()
        schedule = []
        # вывод уроков с учетом замен
        for elem in lessons:
            schedule.append(str(elem[0]) + ' ' + str(elem[1]))
        for elem in rep:
            schedule[elem[0]] = "Замена: " + str(elem[1]) + ' ' + str(elem[2])
        resstr = "\n".join(schedule)
        if resstr:
            await update.message.reply_text('Список уроков на ' + str(td)[5:] + ':')
            await update.message.reply_text(resstr)
        else:
            await update.message.reply_text('У вас нет уроков ' + str(td)[5:] + '!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /reg - команда для регистрации пользователя
async def reg(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и кода, который он ввел
        user_id = str(update.message.from_user.id)
        code = str(context.args[0])
        # пасхалка)
        if code == '1h832f1':
            await update.message.reply_text('Зачем ты регестрируешь код из help? :P')
        else:
            print(code)
            print(user_id)
            codes = con.cursor().execute("""Select code from User""", ()).fetchall()
            ids = con.cursor().execute("""Select telId from User""", ()).fetchall()
            # проверка что код существует
            if (code,) not in codes:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Неверный код!')
            # проверка что id не зарегестрирован
            elif (int(user_id),) in ids:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Ваш id уже зарегестрирован!')
            else:
                id = con.cursor().execute("""Select telId from User WHERE code = ?""", (code,)).fetchone()
                print(id)
                # проверка что код не зарегестрирован
                if id == (None,) or id == ('',):
                    # добавление id в БД
                    con.cursor().execute("""Update User set telId = ? WHERE code = ?""", (user_id, code))
                    con.commit()
                    name = con.cursor().execute("""SELECT name From User WHERE code = ?""", (code,)).fetchone()[0]
                    status = con.cursor().execute("""SELECT status From User WHERE code = ?""", (code,)).fetchone()[0]
                    print(name)
                    if status == 'ученик':
                        resstr = 'Регистрация прошла успешно! Привет, ' + str(name) + '!'
                    else:
                        resstr = 'Регистрация прошла успешно! Здравствуйте, ' + str(status) + '!'
                    await update.message.reply_text(resstr)
                else:
                    await update.message.reply_text('Ошибка')
                    await update.message.reply_text('Этот код уже зарегестрирован!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# функция для отправки текстовых сообщений конкретному пользователю
async def send(chat, msg):
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.send_message(chat_id=chat, text=msg)


# функция для отправки документов конкретному пользователю
async def sendDocument(chat, doc):
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.send_document(chat_id=chat, document=doc)


# /mes_cl - команда для сообщения классу(ам)
async def mes_cl(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        anusersnorm = []
        # проверка что пользователь учитель или админ
        if status == ('учитель',) or status == ('админ',):
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            cl = context.args[0].split(',')
            message = str(context.args[1])
            # проверка на пустое сообщение
            if message:
                # получение списка учеников
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
                # проверка что такой класс есть
                if anusers:
                    # отправка в циукле сообщений ученикам
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /mes_gr - команда для сообщения группе(ам)
async def mes_gr(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        anusersnorm = []
        # проверка что пользователь учитель или админ
        if status == ('учитель',) or status == ('админ',):
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            group = context.args[0]
            message = str(context.args[1])
            # проверка на пустое сообщение
            if message:
                # получение участников по короткому или длинному названию группы
                try:
                    names = \
                        con.cursor().execute("""Select participants from Groups where name= ? """, (group,)).fetchone()[
                            0]
                except:
                    names = \
                        con.cursor().execute("""Select participants from Groups where shortName = ? """,
                                             (group,)).fetchone()[0]
                    names = names.split(',')
                # получение id пользователей
                for i in names:
                    anusers.append(
                        con.cursor().execute("""Select telId from User where name = ? """, (i,)).fetchone()[0]
                    )
                print(anusers)
                # отправление сообщений пользователям
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /mes_st - команда для сообщения ученику(ам)
async def mes_st(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        # проверка что пользователь учитель или админ
        if status == ('учитель',) or status == ('админ',):
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            names = context.args[0].split(',')
            print(names)
            message = str(context.args[1])
            # проверка на пустое сообщение
            if message:
                # получение id пользователей
                for i in names:
                    print(i)
                    anusers.append(
                        con.cursor().execute("""Select telId from User where name = ? """, (i.strip(),)).fetchone())
                print(anusers)
                # отправление сообщений пользователям
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /mes_t - команда для сообщения учителю
async def mes_t(update, context):
    try:
        loop = asyncio.get_event_loop()
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con: Connection = sqlite3.connect(DBNAME)
        # получение id пользователя и его имени
        user_id = str(update.message.from_user.id)
        name = context.args[0]
        teacherst = con.cursor().execute("""Select name from User where status = ? """, ('учитель',)).fetchall()
        teachers = []
        for i in teacherst:
            teachers.append(list(i)[0])
        if name in teachers:
            # получение имени пользователся и черного списка учителя
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            blacklisted = con.cursor().execute("""Select studentName from Blacklist WHERE teacherName = ?""",
                                               (name,)).fetchall()
            print(blacklisted)
            try:
                blacklisted = list(blacklisted[0])[0].split(',')
            except IndexError:
                blacklisted = []
            print(blacklisted)
            # проверка на нахождения ученика в черном списке
            if user_name not in blacklisted:
                message = str(context.args[1])
                # проверка на пустое сообщение
                if message:
                    # отправка сообщений
                    i = con.cursor().execute("""Select telId from User where name = ? """, (name.strip(),)).fetchone()[
                        0]
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /add_rep - команда для создания замен
async def add_rep(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con: Connection = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        stat = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()
        print(context.args)
        # проверка что пользователь учитель или админ
        if stat == ('учитель',) or stat == ('админ',):
            rep = context.args
            # форматирование даты
            rep[0] = "2023-" + rep[0]
            # получение замены
            z = con.cursor().execute(
                """SELECT * FROM Replace WHERE day = ? and classRep = ? and numLesson = ?""",
                (rep[0], rep[1], str(int(rep[2]) - 1))).fetchall()
            print(z)
            # проверка что замена уже есть
            if not z:
                # добавление замены
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /remove_rep - команда для удаления замен
async def remove_rep(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con: Connection = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        stat = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()
        print(context.args)
        # проверка что пользователь учитель или админ
        if stat == ('учитель',) or stat == ('админ',):
            rep = context.args
            rep[0] = "2023-" + rep[0]
            print((rep[0], rep[1], str(rep[2])))
            # удаление замены
            con.cursor().execute(
                """DELETE FROM Replace WHERE day = ? and classRep = ? and numLesson = ? """,
                (rep[0], rep[1], str(int(rep[2]) - 1)))
            con.commit()
            await update.message.reply_text('Замена успешно удалена!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('У вас нет прав на использование этой команды!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /poll - команда для создания опросов
async def poll(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        questions = [context.args[2].split(', ')]
        questions = questions[0]
        print(questions)
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        anusersnorm = []
        # проверка что пользователь учитель или админ
        if status == ('учитель',) or status == ('админ',):
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            print(user_name)
            cl = context.args[0].split(', ')
            for i in cl:
                print(i)
                # получение id опрашиваемых
                anusers.append(con.cursor().execute("""Select telId from User where class = ? """,
                                                    (i.lower().strip(),)).fetchall())
            print(anusers)
            for i in anusers:
                for q in i:
                    anusersnorm.append(q)
            anusers = anusersnorm
            print(anusers)
            typ = len(con.cursor().execute("""Select * from Survey """).fetchall()) + 1
            # проверка на наличие опрашиваемых
            if anusers:
                for i in anusers:
                    if i != (None,) and i and i != ('',):
                        print(i)
                        i = list(i)[0]
                        if str(i) != str(user_id):
                            print(i)
                            loop = asyncio.get_event_loop()
                            # отправление опроса
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
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Некорректный или пустой класс!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# получение результатов опроса
async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
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
        # Close poll after 1000 participants voted
        if answered_poll["answers"] == TOTAL_VOTER_COUNT:
            await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])
        con = sqlite3.connect(DBNAME)
        ans = con.cursor().execute("""Select answer From Survey where id = ?""", (idpoll,)).fetchone()
        print(ans)
        if ans == ('None',):
            user_name = \
                con.cursor().execute("""Select name from User where telId = ? """,
                                     (update.effective_user.id,)).fetchone()[
                    0]
            ansnew = str(answer_string)
            print(user_name)
            con.cursor().execute("update Survey set name = ?, answer = ? WHERE id = ?", (user_name, ansnew, idpoll))
            con.commit()
        print(ans)
        print(update.effective_user.id)
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /poll_ans - команда для получения результатов опроса в формате .xlsx
async def ans_table(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        idpoll = context.args[0]
        print(idpoll)
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его имени
        user_id = str(update.message.from_user.id)
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        # получение имени автора опроса
        author = con.cursor().execute("""Select author From Survey where id = ?""", (idpoll,)).fetchone()[0]
        print(user_name, author)
        # проверка что пользователь автор опроса
        if user_name == author:
            typ = con.cursor().execute("""Select typ From Survey where id = ?""", (str(idpoll),)).fetchall()
            print(typ)
            ans = []
            # for elem in ids:
            answer = con.cursor().execute("""Select name, answer From Survey where typ = ?""", (typ[0][0],)).fetchall()
            for elem in answer:
                if elem[0] != 'None':
                    ans.append(elem)
            print(ans)
            # проверка что опрос кто-либо прошел
            if ans == 'None' or ans == None or ans == ('None',) or ans == []:
                await update.message.reply_text('Опрос ' + str(idpoll) + ' никто ещё не прошел!')
            else:
                # создание таблицы
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /new_user - команда для добавления пользователя
async def new_user(update, context):
    try:
        con = sqlite3.connect(DBNAME)
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        name = context.args[0]
        clas = context.args[1]
        stat = context.args[2]
        # список символов, применимых в коде
        symbols = '0123456789qwertyuiopasdfghjklzxcvbnm'
        print(len(symbols))
        codes = con.cursor().execute("""Select code From User""").fetchall()
        for elem in codes:
            elem = elem[0]
        code = []
        # создание кода из рандомных символов
        while code in codes or len(code) < 8:
            # получение случайного числа от 1 до 36 путем запроса к API random.org
            # на random.org числа генерируются исходя из радиошумов атмосферы, так что подучаемые числа истинно случайны
            # в отличии чисел получаемых random.randint )
            request = requests.get(
                'https://www.random.org/integers/?num=1&min=1&max=36&col=1&base=10&format=plain&rnd=new')
            number = request.json()
            code.append(symbols[number])
        code = ''.join(code)
        # добавление в БД
        con.cursor().execute(
            """INSERT INTO User (name, status, class, code)
             values(?, ?, ?, ?)""",
            (name, stat, clas, code))
        con.commit()
        await update.message.reply_text('Пользователь успешно добавлен! ' + name + " с кодом:" + code)
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /poll_ans - команда для получения результатов опроса
async def poll_ans(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        idpoll = context.args[0]
        con = sqlite3.connect(DBNAME)
        # получение id пользователя, его имени и автора опроса
        user_id = str(update.message.from_user.id)
        user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        author = con.cursor().execute("""Select author From Survey where id = ?""", (idpoll,)).fetchone()[0]
        # Проверка на то что пользователь это автор опроса
        if user_name == author:
            typ = con.cursor().execute("""Select typ From Survey where id = ?""", (idpoll,)).fetchall()
            print(typ)
            ans = []
            # for elem in ids:
            # получение ответов
            answer = con.cursor().execute("""Select name, answer From Survey where typ = ?""", (typ[0][0],)).fetchall()
            for elem in answer:
                if elem[0] != 'None':
                    ans.append(elem)
            print(ans)
            # проверка что опрос кто либо прошел
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /help - команда для помощи по командам
async def help(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con = sqlite3.connect(DBNAME)
        # получение id пользователя
        user_id = str(update.message.from_user.id)
        print(context.args)
        if context.args == ['']:
            # получение статуса пользователя
            status = con.cursor().execute("""Select status From User where telid = ?""", (user_id,)).fetchone()[0]
            # в зависимости от статуса пользователя вывод различной помощи
            if status == 'учитель':
                for key in HELP_DICT_T:
                    await update.message.reply_text(HELP_DICT_T[key][0])
            elif status == 'ученик':
                for key in HELP_DICT_ST:
                    await update.message.reply_text(HELP_DICT_ST[key][0])
        else:
            # если есть аргумент то вывод углубленной помощи по конкретной команде, так же в зависимости от статуса
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /add_gr - команда для добавления человека в группу
async def add_gr(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        # проверка что пользователь админ или учитель
        if status == ('учитель',) or status == ('админ',):
            # получение коротких названий групп
            shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
            print(shortNames)
            sn = []
            for i in shortNames:
                sn.append(list(i)[0])
            print(sn)
            shortNames = sn
            # проверка что группа с таким сокращенеим существует
            if context.args[1] in shortNames:
                participants = con.cursor().execute("""Select participants from Groups WHERE shortName = ?""",
                                                    (context.args[1],)).fetchone()
                participants = participants[0]
                # если в группе никого нет
                if participants is None or not participants:
                    participants = context.args[0]
                    con.cursor().execute("""Update Groups set participants = ? WHERE shortName = ?""",
                                         (participants, context.args[1]))
                    con.commit()
                    gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                              (context.args[1],)).fetchone()
                    await update.message.reply_text(
                        'Пользователь ' + context.args[0] + ' успешно добавлен в группу ' + str(gr[0]))
                # проверка что пользователь не в группе
                elif context.args[0] not in participants.split(','):
                    participants = participants + ',' + context.args[0]
                    con.cursor().execute("""Update Groups set participants = ? WHERE shortName = ?""",
                                         (participants, context.args[1]))
                    con.commit()
                    # добавление пользователя в группу
                    gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                              (context.args[1],)).fetchone()
                    await update.message.reply_text(
                        'Пользователь ' + context.args[0] + ' успешно добавлен в группу ' + str(gr[0]))
                    telId = con.cursor().execute("""Select telId from User WHERE name = ?""",
                                                 (context.args[0],)).fetchone()
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /del_gr - команда для удаления человека из группы
async def del_gr(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        # проверка что пользователь админ или учитель
        if status == ('учитель',) or status == ('админ',):
            shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
            print(shortNames)
            sn = []
            for i in shortNames:
                sn.append(list(i)[0])
            print(sn)
            shortNames = sn
            # проверка что группа с таким сокращенеим существует
            if context.args[1] in shortNames:
                participants = con.cursor().execute("""Select participants from Groups WHERE shortName = ?""",
                                                    (context.args[1],)).fetchone()
                participants = participants[0]
                if participants is None:
                    participants = ''
                # проверка что пользователь в группе
                if context.args[0] in participants.split(','):
                    # удаление пользователя из группы в БД
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /delete_gr - команда для удаления группы
async def delete_gr(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(status)
        anusers = []
        # проверка что пользователь админ или учитель
        if status == ('учитель',) or status == ('админ',):
            shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
            # проверка что группа с таким котортким названием существует
            if context.args[0] in shortNames[0]:
                # удаление пользователя из БД
                gr = con.cursor().execute("""Select name from Groups WHERE shortName = ?""",
                                          (context.args[0],)).fetchone()
                con.cursor().execute("""DELETE from Groups WHERE shortName = ?""", (context.args[0],))
                con.commit()
                await update.message.reply_text('Группа ' + str(gr[0]) + ' успешно удалена')
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Группы с таким сокращением не существует')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('У вас нет прав на использование этой команды!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /create_gr - команда для создания группы
async def create_gr(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        print(45)
        anusers = []
        # проверка что пользователь админ или учитель
        if status == ('учитель',) or status == ('админ',):
            names = con.cursor().execute("""Select name From Groups""").fetchall()
            # проверка что передано 2 аргумента
            if len(context.args) == 2:
                # проверка что такой группы не существует
                if context.args[0] not in names:
                    shortNames = con.cursor().execute("""Select shortName From Groups""").fetchall()
                    # проверка что сокращение нигде не используется
                    if context.args[1] not in shortNames:
                        # добавление группы в БД
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /start - функция для старта работы с ботом
async def start(update, context):
    await update.message.reply_text('SchoolBot v 1.0')
    await update.message.reply_text('Бот для удобного взаимодействия учителей и учеников в школе')
    await update.message.reply_text('Введите /help для помощи по командам')


# /add_bl - команда для добавления ученика в черный список
async def add_bl(update, context):
    try:
        # разделение аргументов по слэшу
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        con = sqlite3.connect(DBNAME)
        name = context.args[0]
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        # получение списка учеников
        userst = con.cursor().execute("""Select name from User where status = ? """, ('ученик',)).fetchall()
        users = []
        # преобразование списка учеников
        for i in userst:
            users.append(list(i)[0])
        print(users)
        # имени учителя
        tname = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        # проверка что пользователь учитель
        if status == ('учитель',):
            # получение черного списка этого учителя
            blacklisted = con.cursor().execute("""Select studentName from Blacklist WHERE teacherName = ?""",
                                               (tname,)).fetchall()
            print(blacklisted)
            # проверка что такой ученик существует
            if name in users:
                # если список пустой то не писать запятую
                if not blacklisted:
                    blacklisted = name
                    # добавление ученика в черный список
                    con.cursor().execute("""insert into Blacklist (studentName, teacherName) values(?, ?)""",
                                         (blacklisted, tname))
                    con.commit()
                    await update.message.reply_text(
                        'Пользователь ' + name + ' успешно добавлен в черный список')
                else:
                    blacklisted = list(blacklisted[0])[0].split(',')
                    # проверка что ученик не в черном списке
                    if name not in blacklisted:
                        blacklisted.append(name)
                        # для соединения списка учеников через запятую
                        blacklisted = ','.join(blacklisted)
                        # добавление ученика в черный список
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /del_bl - команда для удаления ученика из вашего черного списка
async def del_bl(update, context):
    try:
        # получение имени ученика
        name = context.args[0]
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        tname = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
        print(status)
        # проверка что пользователь учитель
        if status == ('учитель',):
            blacklisted = con.cursor().execute("""Select studentName From Blacklist where teacherName = ?""",
                                               (tname,)).fetchall()
            blacklisted = list(blacklisted[0])[0].split(',')
            # проверка что ученик в черном списке
            if name in blacklisted:
                # удаление ученика из черного списка
                blacklisted.remove(name)
                blacklisted = ','.join(blacklisted)
                con.cursor().execute("""Update Blacklist set studentName = ? WHERE teacherName = ?""",
                                     (blacklisted, tname))
                con.commit()
                blacklisted = con.cursor().execute("""Select studentName From Blacklist where teacherName = ?""",
                                                   (tname,)).fetchall()
                blacklisted = list(blacklisted[0])[0].split(',')
                print(blacklisted)
                # если черный список учителя пустой, то удалить строку с его именем в БД
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
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /report - команда для оповещения администраторов
async def report(update, context):
    try:
        # проверка что сообщение не пустое
        if context.args:
            text = context.args[0]
            loop = asyncio.get_event_loop()
            con = sqlite3.connect(DBNAME)
            # получение id пользователя, его имени и статуса
            user_id = str(update.message.from_user.id)
            user_name = con.cursor().execute("""Select name from User where telId = ? """, (user_id,)).fetchone()[0]
            status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()[0]
            # получение списка администраторов
            adminst = con.cursor().execute("""Select telId from User where status = ? """, ('админ',)).fetchall()
            admins = []
            for i in adminst:
                admins.append(list(i)[0])
            print(admins)
            # отправка сообщения с сопутсвующей информацией
            message = 'Вам пришло сообщение от ' + user_name + ', ' + status + ' (Telegram ID: ' + user_id + '):'
            for i in admins:
                await loop.create_task(send(i, message))
                await loop.create_task(send(i, text))
            await update.message.reply_text('Оповещение успешно отправлено')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('Нельзя отправлять оповещение без сообщения!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


# /members - команда для вывода всех учеников класса или группы
async def members(update, context):
    try:
        context.args = ' '.join(update.message.text.split()[1:]).split('/')
        loop = asyncio.get_event_loop()
        con = sqlite3.connect(DBNAME)
        # получение id пользователя и его статуса
        user_id = str(update.message.from_user.id)
        status = con.cursor().execute("""Select status from User where telId = ? """, (user_id,)).fetchone()
        anusers = []
        # проверка что пользователь учитель или администратор
        if status == ('учитель',) or status == ('админ',):
            classes = con.cursor().execute("""Select class from User""").fetchall()
            print(classes)
            groups = con.cursor().execute("""Select shortName from Groups """).fetchall()
            # проверка что есть класс с таким названием
            if (context.args[0],) in classes:
                # получение имен всех учеников класса
                stud = con.cursor().execute("""Select name from User WHERE class = ?""", (context.args[0],)).fetchall()
                print(stud)
                studnorm = []
                for elem in stud:
                    studnorm.append(str(len(studnorm) + 1) + ' ' + elem[0])
                await update.message.reply_text('В классе ' + context.args[0] + ' учатся:')
                await update.message.reply_text('\n'.join(studnorm))
            # проверка что есть группа с таким названием
            elif (context.args[0],) in groups:
                # получение имен всех членов группы
                stud = con.cursor().execute("""Select name, participants from Groups WHERE shortName = ?""",
                                            (context.args[0],)).fetchone()
                name = stud[0]
                stud = stud[1].split(',')
                studnorm = []
                for elem in stud:
                    studnorm.append(str(len(studnorm) + 1) + ' ' + elem)
                print(stud)
                await update.message.reply_text('В группе "' + name + '" состоят:')
                await update.message.reply_text('\n'.join(studnorm))
            else:
                await update.message.reply_text('Ошибка!')
                await update.message.reply_text('Нет такого класса или группы!')
        else:
            await update.message.reply_text('Ошибка!')
            await update.message.reply_text('У вас нет прав на использование этой команды!')
    except:
        await update.message.reply_text('Ошибка!')
        await update.message.reply_text('Непредвиденная ошибка!')
        await update.message.reply_text('Используйте функцию /help, а если не поможет то /report')


def main():
    # добавление команд
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
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("members", members))
    application.run_polling()


if __name__ == '__main__':
    main()
