BOT_TOKEN = '6276405318:AAFjYNJjlDrvRlFiMOZ9er2-pdiiO_uU4Uo'
DBNAME = 'Replaces.db'
TOTAL_VOTER_COUNT = 3
HELP_DICT_ST = {
    'reg': ['/reg - команда для регестрации пользователя',
            'Принимает 1 аргумент - код человека', 'После ввода telegram id человека добавляется в базу данных'
                                                   ' к соответсвующему имени', 'Пример ввода: /reg 1h832f1'],
    'les': ['/les - команда для вывода уроков', 'Не принимает аргументов',
            'После ввода выводит список всех уроков,которые сегодня есть у ученика (включая замены)',
            'Пример ввода: /les']
}
HELP_DICT_T = {
    'announce_cl': ['/announce_cl - команда для оповещения класса(ов)',
                    'Принимает 2 аргумента - класс или классы через запятую и сообщение, которое необходимо отправить',
                    'После ввода всем ученикам этих классов приходит указанное сообщение',
                    'Пример ввода: /announce_cl 7а, 9б, 8в/Объявление:.....'],
    'announce_st': ['/announce_cl - команда для оповещения ученика(ов)',
                    'Принимает 2 аргумента - имя ученика или имена через запятую и сообщение,'
                    ' которое необходимо отправить',
                    'После ввода всем ученикам приходит указанное сообщение',
                    'Пример ввода: /announce_st Рома, Паша, Федя/Объявление:.....'],
    'poll': ['/poll - команда для создания опросов', 'Принимает 3 аргумента - класс или классы через запятую,'
                                                     'Название опроса и варианты ответов через запятую',
             'После ввода всем ученикам этих классов приходит опрос а учителю ID опроса в системе',
             'Пример ввода: /poll 9а, 7б/любимая цифра/0, 1, 2, 3, 4, 5, 6, 7, 8, 9'],
    'poll_ans': ['/poll_ans - команда для получения результатов опроса', 'Принимает 1 аругмент - ID опроса',
                 'После ввода выводит имена уеников и их ответы', 'Пример ввода: /poll_ans 1567'],
    'ans_table': ['/poll_ans - команда для получения результатов опроса в формате .xlsx',
                  'Принимает 1 аругмент - ID опроса', 'После ввода выводит файл с резульатами',
                  'Пример ввода: /ans_table 1567'],
    'add_rep': ['/add_rep - команда для создания замен',
                'Принимает 5 аргументов - дата, класс, номер урока, который будут замещать, название нового урока,'
                ' кабинет в котором будет проходить замена', 'После ввода в базе данных появляется новая замена',
                'Пример ввода: /add_rep 05-17/9а/6/Алгебра/405'],
    'remove_rep': ['/remove_rep - команда для удаления замен',
                   'Принимает 3 аргумента - дата, класс и номер урока, в который удаляется замена',
                   'После ввода из базы данных удаляется замена', 'Пример ввода: /remove_rep 04-18/9а/6'],
    'new_user': ['/new_user - команда для добавления пользователя',
                 'Принимает 3 аргумента - имя пользователя, класс, статус',
                 'После ввода в базу данных добавляется пользователь и выводтся его код',
                 'Пример ввода: /new_user Миша/9б/ученик']
}
