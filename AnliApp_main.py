import telebot
import sqlite3
import traceback
import time
from itertools import zip_longest
from telebot import TeleBot, types


token = ''
bot = telebot.TeleBot(token)
id_send = '-1001884350546' # В какой чат отправить информацию об использовании
administrator = 'kurillccc' # Кого не учитываем при отправке
table_with_mailling_list = 'maillig_list'

conn = sqlite3.connect('BaseD_anki.db', check_same_thread=False)
cursor = conn.cursor()

### Код для администратора (отправка сообщений)
### --- Функция для отправки сообщения всем пользователям
@bot.message_handler(commands=['send'])
def send(message):
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    if (message.from_user.username == administrator):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Send to all users", callback_data='all_users')
        btn2 = types.InlineKeyboardButton("Show all users", callback_data='show_all_users')
        btn3 = types.InlineKeyboardButton("Send to one specific user", callback_data='specific_user')
        btn4 = types.InlineKeyboardButton("Close", callback_data='close')
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(btn4)
        bot.send_message(chat_id, f'Choose an action:', reply_markup=markup)
        bot.callback_query_handler(func=settings_for_administration)
    else:
        bot.send_message(id_send, f'⚠️@{message.from_user.username} пытался воспользоваться командой send ⚠️\nUser id: {message.from_user.id} \nUser name: {user_name}\n🤖: AnliApp_bot ')  # Отправка сообщения в канал
        return
@bot.callback_query_handler(func=lambda call: call.data in ['all_users', 'show_all_users', 'specific_user', 'close'])
def settings_for_administration(call):
    if (call.data == 'all_users'):
        msg = bot.send_message(call.message.chat.id, f'Write the text:\n(write /stop to stop)')
        bot.register_next_step_handler(msg, all_users_send)
    elif (call.data == 'show_all_users'):
        chat_id = show_the_all_table_2('user_id')
        name = show_the_all_table_2('username')
        result = array_sum(chat_id, name)
        bot.send_message(call.message.chat.id, f'{result}')
    elif (call.data == 'specific_user'):
        msg = bot.send_message(call.message.chat.id, f'Send the user\'s chat id:\n(write /stop to stop)')
        bot.register_next_step_handler(msg, specific_user)
    elif (call.data == 'close'):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return

# Для отравки сообщения всем пользователям
def all_users_send(message):
    if (message.text == '/stop'):
        return
    text = message.text
    cursor.execute(f"SELECT * FROM {table_with_mailling_list}")
    result = cursor.fetchall()
    column_index = 1  # индекс колонки с чат id
    column = [row[column_index] for row in result]
    if message.photo:
        photo = message.photo[-1]  # берем последнее (наилучшее) фото из списка
        file_id = photo.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        for id in column:
            try:
                caption = message.caption if message.caption is not None else ""
                bot.send_photo(id, file, caption=caption, parse_mode='HTML')
            except telebot.apihelper.ApiException as e:
                if e.result.status_code == 403:
                    try:
                        us_id = "user_" + str(id)
                        drop_table = f"DROP TABLE {us_id};"
                        cursor.execute(drop_table)
                        conn.commit()
                    except:
                        pass
    else:
        for id in column:
            try:
                send_message_to_user(id, text)
            except telebot.apihelper.ApiException as e:
                if e.result.status_code == 403:
                    try:
                        us_id = "user_" + str(id)
                        drop_table = f"DROP TABLE {us_id};"
                        cursor.execute(drop_table)
                        conn.commit()
                    except:
                        pass

# Для обработки сообщения с конкретным пользователем
def specific_user(message):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        return
    if (message.text == '/stop'):
        return
    user_id = int(message.text)
    text = bot.send_message(message.chat.id, f'Write the text\n(write /stop to stop)')
    bot.register_next_step_handler(text, send_text_specific_user, user_id)
def send_text_specific_user(message, user_id):
    if (message.text == '/stop'):
        return
    text = message.text
    if message.photo:
        # Получаем информацию о фото
        photo = message.photo[-1]  # берем последнее (наилучшее) фото из списка
        file_id = photo.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        try:
            # Получаем текстовое сообщение, которое пришло с фото (если есть)
            caption = message.caption if message.caption is not None else ""
            # Отправляем фото и текст обратно пользователю
            bot.send_photo(user_id, file, caption=caption, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, f'Not sent')
            return
        bot.send_message(message.chat.id, f'Successfully')
    else:
        try:
            send_message_to_user(user_id, text)
        except:
            bot.send_message(message.chat.id, f'Not sent')
            return
        bot.send_message(message.chat.id, f'Successfully')

# Для отправки сообщения пользователю
def send_message_to_user(user_id: int, text: str):
    bot.send_message(user_id, f'{text}', parse_mode="html".format(user_id))

# Для создания таблицы (чтобы в случае переноса бота, не создавать в базе данных таблицу вручную)
def pass_in_maillig_list(user_id: int, username: str, user_name: str, user_sername: str):
    cursor.execute('''CREATE TABLE {}
                            (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                            user_id INTEGER UNIQUE,
                            username TEXT,
                            user_name TEXT,
                            user_sername TEXT)'''.format(table_with_mailling_list))
    cursor.execute(f'INSERT INTO {table_with_mailling_list} (user_id, username, user_name, user_sername) VALUES (?, ?, ?, ?)', (user_id, username, user_name, user_sername))
    conn.commit()
#####################
# Функция для создания профиля (создается таблица с названием user_id и инициализирует столбы)
# Некоторые столбцы инициализируются, а некоторые нет
def create_table_and_pass(user_id: int, user_name: str, user_sername: str):
    us_id = "user_" + str(user_id)
    cursor.execute('''CREATE TABLE {}
                (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                user_id INTEGER UNIQUE, 
                user_name TEXT,
                user_sername TEXT,
                first_word TEXT,
                second_word TEXT,
                count_of_solves INTEGER,
                co_solves_per_one INTEGER,
                mode INTEGER,
                point INTEGER,
                sol_help INTEGER,
                sorted_matrix TEXT)'''.format(us_id))
    cursor.execute(f'INSERT INTO {us_id} (user_id, user_name, user_sername, count_of_solves, co_solves_per_one, mode, point, sol_help) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, user_name, user_sername, 0, 20, 0, 0, 0))
    conn.commit()
# Функция, которая нужна непосредственно для работы с таблицей (вставка слов)
def pass_words(user_id: int, first_word: str, second_word: str):
    us_id = "user_" + str(user_id)
    cursor.execute(f'INSERT INTO {us_id} (first_word, second_word, point) VALUES (?, ?, ?)', (first_word, second_word, 0))
    conn.commit()
# Функция чтобы вставить какое-то значение численное
def pass_value(user_id: int, value, row_number: int, column_name: str):
    us_id = "user_" + str(user_id)
    cursor.execute(f"UPDATE {us_id} SET {column_name}=? WHERE rowid=?", (value, row_number))
    conn.commit()
# Число карточек
def count_of_cards(user_id: int):
    us_id = "user_" + str(user_id)
    cursor.execute(f"SELECT * FROM {us_id}")
    return (len(cursor.fetchall())-1)
def array_sum(arr1, arr2):
    result = "".join([f"📌 {a}   -   {b}\n" for a, b in zip(arr1, arr2)])
    return result
# Функция, которая возврощает всю таблицу за исключением первого элемента
def show_the_card(user_id: int):
    us_id = "user_" + str(user_id)
    cursor.execute(f"SELECT * FROM {us_id}")
    result = cursor.fetchall()
    del result[0]
    return result
# Возврощает всю таблицу вместе с первой строкой
def show_the_first_string(user_id: int):
    us_id = "user_" + str(user_id)
    cursor.execute(f"SELECT * FROM {us_id}")
    result = cursor.fetchall()
    return result
# Функция для получения всей колонки по ее номеру (нумерация как в массиве)
def show_the_column(user_id: int, i: int):
    # i индекс колонки
    us_id = "user_" + str(user_id)
    cursor.execute(f"SELECT * FROM {us_id}")
    result = cursor.fetchall()
    column_index = i # индекс нужной колонки
    column = [row[column_index] for row in result] # получаем список элементов из последней колонки
    return column
def show_the_all_table_2(name_of_the_column: str): # тут сортирвовка по id иначе код будет неправильно все выдавать (именно числа)
    cursor.execute(f"SELECT {name_of_the_column} FROM {table_with_mailling_list} ORDER BY id")
    res = cursor.fetchall()  # записали столбец
    result_array = [r[0] for r in res]
    return result_array
# Функция для вывода всех карточек из колоды
def show_the_all_table(user_id: int, name_of_the_table: str):
    us_id = "user_" + str(user_id)
    cursor.execute(f"SELECT {name_of_the_table} FROM {us_id}")
    res = cursor.fetchall() # записали столбец
    result_array = []
    for r in res:
        result_array.append(r[0]) # append добавляет в конце списка элемент
    return result_array
# Функция для изменения чего либа в таблице и не только слова
def edit_card(user_id: int, name_of_the_table: str, id_of_dest: int, new_value):
    us_id = "user_" + str(user_id)
    cursor.execute(f"UPDATE {us_id} SET {name_of_the_table} = ? WHERE id = ?", (new_value, id_of_dest))
    conn.commit()
# Функция для склейки двух массив [cat - dog, parrot - scar and ect.]
def glue_two_arrays(arr1, arr2):
# Склеиваем два массива используя zip(), которая объединит элементы обоих массивов в кортежи,
# а затем объединить элементы кортежей с помощью строкового метода `join()`
    result = [arr1 + ' - ' + arr2 for arr1, arr2 in zip(arr1, arr2)]
    return result
# Функция для очистки всей таблицы (start - с какой строки начать (ее саму не трогает))
def del_the_deck(user_id: int, start: int): # удаляет все что больше конкретной строки start
    us_id = "user_" + str(user_id)
    sql_query = f"DELETE FROM {us_id} WHERE id >= {start}"
    # выполняем запрос на удаление строк
    cursor.execute(sql_query)
    conn.commit()
# Функция для поиска элемента в таблице
def find_word(user_id: int, table_name_1: str, table_name_2: str, word1: str, word2: str):
    us_id = "user_" + str(user_id)
    query = f"SELECT * FROM {us_id} WHERE {table_name_1} LIKE '%{word1}%' AND {table_name_2} LIKE '%{word2}%'"
    cursor.execute(query)
    results = cursor.fetchall()
    return results[0][0] # возврощает номер строки с двумя нужными нам словами
# Функция для удаления карточки если мы знаем номер строки
def dell_card_by_number(user_id: int, row_number: int):
    us_id = "user_" + str(user_id)
    cursor.execute(f'DELETE FROM {us_id} WHERE id = ?', (row_number,))
    conn.commit()
# Функция, чтобы показать строку по ее номеру
def show_card_by_number_of_row(user_id: int, row_number: int):
        us_id = "user_" + str(user_id)
        cursor.execute(f'SELECT * FROM {us_id} WHERE rowid = ?', (row_number,))
        row = cursor.fetchone()
        return row
# Функция для проверки режима карточек
def view_mode(user_id: int):
    result = show_the_first_string(user_id)
    if (int(result[0][8]) == 0):
        return "Лицевая - обратная"
    elif (int(result[0][8]) == 1):
        return "Обратная - лицевая"
################################################
################################################
# Начало основного кода
@bot.message_handler(commands=['start'])
def start(message):
    username = '@' + message.from_user.username
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    user_sername = message.from_user.last_name
    try:
        cursor.execute(f'INSERT INTO {table_with_mailling_list} (user_id, username, user_name, user_sername) VALUES (?, ?, ?, ?)',(chat_id, username, user_name, user_sername))
        conn.commit()
    except:
        try:
            pass_in_maillig_list(chat_id, username, user_name, user_sername)
        except:
            pass
    if message.from_user.username != administrator:
        bot.send_message(id_send, f'@{message.from_user.username} нажал(-а) "/start"\nUser id: {message.from_user.id} \nUser name: {user_name}\n🤖: AnliApp_bot ')  # Отправка сообщения в канал
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📍 Начать")
    btn2 = types.KeyboardButton("🔑 Профиль")
    btn3 = types.KeyboardButton("🛠 Настройки")
    btn4 = types.KeyboardButton("🔔 Информация")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)

    us_id = "user_" + str(chat_id)
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (us_id,))
    result = cursor.fetchone()

    if result:
        bot.send_message(chat_id, text="Добро пожаловать, Ваш профиль уже существует!".format(message.from_user),reply_markup=markup)
    else:
        bot.send_message(chat_id, text=f"Добро пожаловать, Ваш профиль успешно создан!", parse_mode="html".format(message.from_user),reply_markup=markup)
        try:
            user_id = message.from_user.id
            user_name = message.from_user.first_name
            user_sername = message.from_user.last_name
            create_table_and_pass(user_id, user_name, user_sername)
        except:
            print(f"Ошибка создания профиля для {message.from_user.first_name}, @{user_id}")
            pass
# Главное меню с кнопками в клавиатуре
@bot.message_handler(content_types=['text'])
def main_window(message):
    chat_id = message.chat.id
    if(message.text == "📍 Начать"):
        us_id = "user_" + str(chat_id)
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{us_id}';")
        result = cursor.fetchall()
        if len(result) == 0:
            bot.send_message(chat_id, f'Напишите в чат /start, чтобы создать профиль')
            pass_value(chat_id, 0, 1, 'sol_help')
            return
        else:
            pass
        ############################
        pass_value(chat_id, 0, 1, 'sol_help')
        if (int(count_of_cards(chat_id)) != 0):
            result = show_the_first_string(chat_id)
            if (int(result[0][7]) > count_of_cards(chat_id)):
                choice_count = count_of_cards(chat_id)
            else:
                choice_count = int(result[0][7])
            bot.send_message(chat_id, f'<b>Начинаю сессию</b>\nРешайте карточки до тех пор, пока не решите {choice_count} карточек или не прервёте сессию одной из кнопок\n',parse_mode="html".format(chat_id))
            matrix = show_the_card(chat_id)
            sorted_matrix = sorted(matrix, key=lambda x: x[9])
            pass_value(chat_id, str(sorted_matrix), 1, 'sorted_matrix')
            time.sleep(0.5)
            start_solving(chat_id)
        else:
            bot.send_message(chat_id, f'Для того, чтобы начать нужно иметь как минимум одну карточку\n<i>(Для создания перейди в: профиль >> создать карточку)</i>', parse_mode='html')
    elif (message.text == "🔑 Профиль"):
        us_id = "user_" + str(chat_id)
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{us_id}';")
        result = cursor.fetchall()
        if len(result) == 0:
            bot.send_message(chat_id, f'Напишите в чат /start, чтобы создать профиль')
            return
        else:
            pass
        ##############
        # Создаем индивидуальную таблицу для пользователя
        count_of_solving = int((show_the_first_string(chat_id))[0][6])
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Создать карточку", callback_data='create_the_card')
        button2 = types.InlineKeyboardButton("Показать колоду", callback_data='show_the_card')
        button3 = types.InlineKeyboardButton("Изменить колоду", callback_data='edit_the_deck')
        button4 = types.InlineKeyboardButton("Удалить колоду", callback_data='del_the_deck')
        button5 = types.InlineKeyboardButton("Вернуться", callback_data='into_main_menu')
        markup.add(button1)
        markup.add(button2)
        markup.add(button3)
        markup.add(button4)
        markup.add(button5)
        bot.send_message(chat_id, f'<U><b>Ваш профиль:</b></U>\n\nЧисло карточек: {count_of_cards(chat_id)}\nРешено карточек всего: {count_of_solving}', parse_mode="html".format(chat_id), reply_markup=markup)
        bot.callback_query_handler(func=actions_with_cards)
    elif (message.text == "🛠 Настройки"):
        us_id = "user_" + str(chat_id)
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{us_id}';")
        result = cursor.fetchall()
        if len(result) == 0:
            bot.send_message(chat_id, f'Напишите в чат /start, чтобы создать профиль')
            return
        else:
            pass
        ##############################################################
        count_per_ses = int(show_the_first_string(chat_id)[0][7])
        mode = view_mode(chat_id)
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Изменить количество карточек за раз", callback_data='change_co_per')
        button2 = types.InlineKeyboardButton("Изменить режим", callback_data='change_mode')
        button3 = types.InlineKeyboardButton("Вернуться", callback_data='go_to_main_menu')
        markup.add(button1)
        markup.add(button2)
        markup.add(button3)
        bot.send_message(chat_id, f'<U><b>Настройки:</b></U>\n\n<b>• Количество карточек за сессию:</b> {count_per_ses}\n<i>(учитывается, если число карточек > или = {count_per_ses})</i>\n\n<b>• Режим карточек:</b> {mode}', parse_mode="html".format(message.chat.id), reply_markup=markup)
        bot.callback_query_handler(func=settings)
    elif (message.text == "🔔 Информация"):
        us_id = "user_" + str(chat_id)
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{us_id}';")
        result = cursor.fetchall()
        if len(result) == 0:
            bot.send_message(chat_id, f'Напишите в чат /start, чтобы создать профиль')
            return
        else:
            pass
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Тех. поддержка", url='https://t.me/kurillccc')
        markup.add(button1)
        bot.send_message(chat_id, f'<U><b>Информация:</b></U>\n\nAnli App - это бот для решения карточек, который использует умную систему для эффективного запоминания информации. Пользователи могут создавать до 1000 карточек самостоятельно, добавлять в них свои вопросы и ответы, а также настраивать бота под свои предпочтения.\n\nВ целом, Anli App - это удобный и эффективный инструмент для тех, кто хочет эффективно учиться и запоминать информацию при помощи карточек.'.format(message.from_user), parse_mode="html", reply_markup=markup)
        return

# Далее основная часть бота с реализацией просмотра карточек и взаимодействия с ними
@bot.callback_query_handler(func=lambda call: call.data in ['create_the_card', 'show_the_card', 'del_the_deck', 'edit_the_deck', 'accept.del', 'decline.del', 'edit_the_card_new', 'into_main_menu'])
def actions_with_cards(call):
    if call.message:
        if call.data == 'create_the_card':
            if (count_of_cards(call.message.chat.id) < 1200):
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Введите первое слово:', reply_markup=None)
                bot.register_next_step_handler(msg, ask_next_word)
            else:
                bot.send_message(chat_id=call.message.chat.id, text=f'К сожалению Вы не можете создать больше карточек\nОбратитесь в тех поддержку')
        elif call.data == 'show_the_card':
            if (count_of_cards(call.message.chat.id) == 0):
                bot.send_message(chat_id=call.message.chat.id, text=f'Ваша колода пуста')
                return
            words_one = show_the_all_table(call.message.chat.id, 'first_word')
            words_two = show_the_all_table(call.message.chat.id, 'second_word')
            del words_one[0]
            del words_two[0]
            result = array_sum(words_one, words_two)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
            markup.add(button1)
            if (len(result) < 4061):
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=  f'<b>Лицевая сторона - тыльная сторона</b>\n{result}', parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            elif (len(result) > 4060 and len(result) < 8000):
                # если число сиволов привышает то делем на 2
                result1 = result[:len(result)//2]
                result2 = result[len(result)//2:]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=  f'<b>Лицевая сторона - тыльная сторона</b>\n{result1}', parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=  f'{result2}', parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            elif (len(result) > 7999 and len(result) < 16000):
                result1 = result[:len(result) // 2]
                result2 = result[len(result) // 2:]

                result1_1 = result1[:len(result1) // 2]
                result1_2 = result1[len(result1) // 2:]
                result2_1 = result2[:len(result2) // 2]
                result2_2 = result2[len(result2) // 2:]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'<b>Лицевая сторона - тыльная сторона</b>\n{result1_1}',parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=f'{result1_2}',parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=f'{result2_1}',parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=f'{result2_2}',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            else:
                bot.send_message(chat_id=call.message.chat.id, text=f'К сожалению вывести карточки невозможно, обратитесь в тех поддержку',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=actions_with_cards)
        elif call.data == 'edit_the_deck':
            if (count_of_cards(call.message.chat.id) == 0):
                bot.send_message(chat_id=call.message.chat.id,text=f'Ваша колода пуста')
                return
            array1 = show_the_all_table(call.message.chat.id, 'first_word')
            array2 = show_the_all_table(call.message.chat.id, 'second_word')
            del array1[0]
            del array2[0] # Удаляем чтобы не было none_type
            arr = glue_two_arrays(array1, array2)
            result = '\n'.join([f"<b><i>{i + 1})</i></b> {elem}" for i, elem in enumerate(arr)])
            if (len(result) < 4061):
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'{result}',parse_mode="html".format(call.message.chat.id), reply_markup=None)
                msg = bot.send_message(chat_id=call.message.chat.id, text=f'<b>Введите номер карточки, которую хотите изменить:</b>',parse_mode="html".format(call.message.chat.id))
            elif (len(result) > 4060 and len(result) < 8000):
                #если число сиволов привышает то делем на 2
                bot.send_message(chat_id=call.message.chat.id, text=f'{len(result)}')
                result1 = result[:len(result)//2]
                result2 = result[len(result)//2:]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'{result1}',parse_mode="html".format(call.message.chat.id), reply_markup=None)
                bot.send_message(chat_id=call.message.chat.id, text=  f'{result2}', parse_mode="html".format(call.message.chat.id), reply_markup=None)
                msg = bot.send_message(chat_id=call.message.chat.id, text=f'<b>Введите номер карточки, которую хотите изменить:</b>',parse_mode="html".format(call.message.chat.id))
            elif (len(result) > 7999 and len(result) < 16000):
                result1 = result[:len(result) // 2]
                result2 = result[len(result) // 2:]

                result1_1 = result1[:len(result1) // 2]
                result1_2 = result1[len(result1) // 2:]
                result2_1 = result2[:len(result2) // 2]
                result2_2 = result2[len(result2) // 2:]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'{result1_1}',parse_mode="html".format(call.message.chat.id), reply_markup=None)
                bot.send_message(chat_id=call.message.chat.id, text=f'{result1_2}',parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=f'{result2_1}',parse_mode="html".format(call.message.chat.id))
                bot.send_message(chat_id=call.message.chat.id, text=f'{result2_2}',parse_mode="html".format(call.message.chat.id))
                msg = bot.send_message(chat_id=call.message.chat.id, text=f'<b>Введите номер карточки, которую хотите изменить:</b>',parse_mode="html".format(call.message.chat.id))
            else:
                bot.send_message(chat_id=call.message.chat.id, text=f'К сожалению вывести карточки невозможно, обратитесь в тех поддержку',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.register_next_step_handler(msg, the_number_of_card, arr)
        elif call.data == 'come_back':
            count_of_solving = int((show_the_first_string(call.message.chat.id))[0][6])
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Создать карточку", callback_data='create_the_card')
            button2 = types.InlineKeyboardButton("Показать колоду", callback_data='show_the_card')
            button3 = types.InlineKeyboardButton("Изменить колоду", callback_data='edit_the_deck')
            button4 = types.InlineKeyboardButton("Удалить колоду", callback_data='del_the_deck')
            button5 = types.InlineKeyboardButton("Вернуться", callback_data='into_main_menu')
            markup.add(button1)
            markup.add(button2)
            markup.add(button3)
            markup.add(button4)
            markup.add(button5)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'<U><b>Ваш профиль:</b></U>\n\nЧисло карточек: {count_of_cards(call.message.chat.id)}\nРешено карточек всего: {count_of_solving}', parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            # в числе карточек стоит минус так как при создании профиля у нас создается
            # пустая строка
            bot.callback_query_handler(func=actions_with_cards)
        elif call.data == 'del_the_deck':
            #    подтверждение удаления всей колоды
            if (count_of_cards(call.message.chat.id) > 0):
                markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton("✅ Да", callback_data='accept.del')
                button2 = types.InlineKeyboardButton("❌ Нет", callback_data='decline.del')
                markup.add(button1, button2)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Вы точно хотите удалить все карточки?', reply_markup=markup)
                bot.callback_query_handler(func=actions_with_cards)
            else:
                bot.send_message(chat_id=call.message.chat.id, text=f'Ваша колода итак пуста')
                return
        elif call.data == 'accept.del':
            count = count_of_cards(call.message.chat.id)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Колода из {count_of_cards(call.message.chat.id)} карточек успешно удалена', reply_markup=markup)
            del_the_deck(call.message.chat.id, 2)
            bot.callback_query_handler(func=actions_after_creating_the_cards)
        elif call.data == 'decline.del':
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Удаление колоды отменено', reply_markup=markup)
            bot.callback_query_handler(func=actions_after_creating_the_cards)
        elif call.data == 'into_main_menu':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'<b>Главное меню:</b>', parse_mode="html".format(call.message.chat.id), reply_markup=None)
            return
# Тут действия после создания карточки
@bot.callback_query_handler(func=lambda call: call.data in ['continue_creating_cards', 'edit_the_card', 'come_back'])
def actions_after_creating_the_cards(call):
    if call.message:
        if call.data == 'continue_creating_cards':
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,reply_markup=None)
            msg = bot.send_message(chat_id=call.message.chat.id, text='Введите первое слово:', reply_markup=None)
            bot.register_next_step_handler(msg, ask_next_word)
        elif call.data == 'edit_the_card':
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Введите первое слово:', reply_markup=None)
            bot.register_next_step_handler(msg, ask_next_new_word)
        elif call.data == 'come_back':
            count_of_solving = int((show_the_first_string(call.message.chat.id))[0][6])
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Создать карточку", callback_data='create_the_card')
            button2 = types.InlineKeyboardButton("Показать колоду", callback_data='show_the_card')
            button3 = types.InlineKeyboardButton("Изменить колоду", callback_data='edit_the_deck')
            button4 = types.InlineKeyboardButton("Удалить колоду", callback_data='del_the_deck')
            button5 = types.InlineKeyboardButton("Вернуться", callback_data='into_main_menu')
            markup.add(button1)
            markup.add(button2)
            markup.add(button3)
            markup.add(button4)
            markup.add(button5)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'<U><b>Ваш профиль:</b></U>\n\nЧисло карточек: {count_of_cards(call.message.chat.id)}\nРешено карточек всего: {count_of_solving}', parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            # в числе карточек стоит минус так как при создании профиля у нас создается
            # пустая строка
            bot.callback_query_handler(func=actions_with_cards)
###########################################################
def ask_next_word(message):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    if (len(message.text) > 70):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    first_word = message.text
    msg = bot.send_message(message.chat.id, text="Введите второе слово:")
    bot.register_next_step_handler(msg, save_card, first_word)
def save_card(message, first_word):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    if (len(message.text) > 70):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    second_word = message.text
    user_id = message.from_user.id
    pass_words(user_id , first_word, second_word)
    conn.commit()
    # Выборка после добавления карточки
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Продолжить", callback_data='continue_creating_cards')
    button2 = types.InlineKeyboardButton("Изменить", callback_data='edit_the_card')
    button3 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
    records = show_the_card(message.chat.id) # тут записывает всю таблицу а с помощью
                                             # records[2] мы можем выбирать конкретную строчку,
                                             # но нам надо получить слово а не строчку
    markup.add(button1, button2,button3)  # Для создания inline нужно
                                          # прописывать (callback_data), чтобы потом
                                          # реагировать на выборку
    bot.send_message(message.chat.id, f'Карточка успешно добавлена!\n{records[-1][-8]} - {records[-1][-7]}', reply_markup=markup)
    bot.callback_query_handler(func=actions_after_creating_the_cards)
# Действия при изменении карточки
def ask_next_new_word(message):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    if (len(message.text) > 55):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    first_new_word = message.text
    msg = bot.send_message(message.chat.id, text="Введите второе слово:")
    bot.register_next_step_handler(msg, save_new_card, first_new_word)
def save_new_card(message, first_new_word):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    if (len(message.text) > 55):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    new_word_1 = first_new_word
    new_word_2 = message.text
    edit_card(message.chat.id, "first_word",  cursor.lastrowid, new_word_1) # Функции которые были определены ранее
    edit_card(message.chat.id, "second_word",  cursor.lastrowid, new_word_2)
    edit_card(message.chat.id, "point", cursor.lastrowid, 0)
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Продолжить", callback_data='continue_creating_cards')
    button2 = types.InlineKeyboardButton("Изменить", callback_data='edit_the_card')
    button3 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
    records = show_the_card(message.chat.id)  # тут записывает всю таблицу а с помощью
                                              # records[2] мы можем выбирать конкретную строчку,
                                              # но нам надо получить слово а не строчку
    markup.add(button1, button2,button3)  # Для создания inline нужно прописывать
                                          # (callback_data), чтобы потом реагировать на выборку
    bot.send_message(message.chat.id, f'Карточка успешно изменена!\n{records[-1][-8]} - {records[-1][-7]}',reply_markup=markup)
    bot.callback_query_handler(func=actions_after_creating_the_cards)
# Функция для определения строки по двум словам из колоды
def the_number_of_card(message, arr):
    try:
        number = int(message.text) - 1
    except:
        bot.send_message(message.chat.id, f'Ошибка чтения данных\n(вводиться должно только целое число)')
        return
    if (len(message.text) > 9):
        bot.send_message(message.chat.id, "Число слишком длинное!")
        return
    try:
        first_word_ = arr[number].split("-")[0].strip() # получаем первое число в каком то элементе
        second_word_ = arr[number].split("-")[1].strip() # до символа "-"
    except:
        bot.send_message(message.chat.id, f'Номера данной карточки не существует')
        return
    number_of_string = find_word(message.chat.id, 'first_word', 'second_word', first_word_, second_word_)
    records = show_the_card(message.chat.id)
    # Выборка после набора номера карточки с которой будет что то происходить
    callback_data1 = f'button_pressed_del:{number_of_string}'
    callback_data2 = f'button_pressed_edit:{number_of_string}' # Делаю так чтобы передать в inline обработчик
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Удалить", callback_data=callback_data1)
    button2 = types.InlineKeyboardButton("Изменить", callback_data=callback_data2)
    button3 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
    records = show_the_card(message.chat.id)  # тут записывает всю таблицу а с помощью
    # records[2] мы можем выбирать конкретную строчку,
    # но нам надо получить слово а не строчку
    markup.add(button2, button1, button3)  # Для создания inline нужно
    # прописывать (callback_data), чтобы потом
    # реагировать на выборку
    bot.send_message(message.chat.id, f'{number+1}) {records[number][-8]} - {records[number][-7]}',reply_markup=markup)
    bot.callback_query_handler(func=inline_button_after_edit_deck)

def edit_the_card_new_1(message, number_of_string):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    first_word_1 = message.text
    if (len(message.text) > 55):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    msg = bot.send_message(message.chat.id, text="Введите второе слово:")
    bot.register_next_step_handler(msg, edit_the_card_new_2, first_word_1, number_of_string)
def edit_the_card_new_2(message, first_word_1, number_of_string):
    if (message.text == "📍 Начать") or (message.text == "🔑 Профиль") or (message.text == "🛠 Настройки") or (message.text == "🔔 Информация"):
        bot.send_message(message.chat.id, text="Неверный формат слова")
        return
    if (len(message.text) > 55):
        bot.send_message(message.chat.id, "Слово или словосочетание слишком длинное!")
        return
    second_word_1 = message.text
    user_id = message.from_user.id
    edit_card(user_id, 'first_word', number_of_string, first_word_1)
    edit_card(user_id, 'second_word', number_of_string, second_word_1)
    edit_card(message.chat.id, "point", number_of_string, 0)
    conn.commit()
    # Выборка после добавления карточки
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Продолжить", callback_data='edit_the_deck')
    button3 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
    records = show_the_card(message.chat.id) # тут записывает всю таблицу а с помощью
                                             # records[2] мы можем выбирать конкретную строчку,
                                             # но нам надо получить слово а не строчку
    markup.add(button1, button3)  # Для создания inline нужно
                                          # прописывать (callback_data), чтобы потом
                                          # реагировать на выборку
    bot.send_message(message.chat.id, f'Карточка успешно изменена!\n{first_word_1} - {second_word_1}', reply_markup=markup)
    bot.callback_query_handler(func=actions_with_cards)
# Далее основная часть - решение карточек и настройки к этим карточкам
@bot.callback_query_handler(func=lambda call: call.data in ['change_co_per', 'change_mode', 'go_to_main_menu', 'go_to_settings'])
def settings(call):
    if call.message:
        if call.data == 'change_co_per':
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("10", callback_data='10')
            button2 = types.InlineKeyboardButton("15", callback_data='15')
            button3 = types.InlineKeyboardButton("20", callback_data='20')
            button4 = types.InlineKeyboardButton("Свое число", callback_data='Own')
            button5 = types.InlineKeyboardButton("Вся колода", callback_data='All')
            button6 = types.InlineKeyboardButton("Вернуться", callback_data='come_back_into_settings')
            markup.add(button1, button2, button3)
            markup.add(button4, button5, button6)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Выберите желаемое количество прорешиваний за раз:', reply_markup=markup)
            bot.callback_query_handler(func=actions_with_settings)
        elif call.data == 'change_mode':
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Лицевая - обратная", callback_data='standart_mode')
            button2 = types.InlineKeyboardButton("Обратная - лицевая", callback_data='revers_mode')
            button3 = types.InlineKeyboardButton("Вернуться", callback_data='come_back_into_settings')
            markup.add(button1)
            markup.add(button2)
            markup.add(button3)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'<b>Выберите режим:</b>',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=actions_with_settings)
        elif call.data == 'go_to_main_menu':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'<b>Главное меню:</b>', parse_mode="html".format(call.message.chat.id), reply_markup=None)
            return

@bot.callback_query_handler(func=lambda call: call.data in ['10', '15', '20', '10', 'Own', 'All', 'come_back_into_settings', 'standart_mode', 'revers_mode'])
def actions_with_settings(call):
    if call.message:
        if call.data == '10':
            edit_card(call.message.chat.id, 'co_solves_per_one', 1, 10)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_co_per')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Количество прорешиваний изменено на: 10',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=settings)
        elif call.data == '15':
            edit_card(call.message.chat.id, 'co_solves_per_one', 1, 15)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_co_per')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Количество прорешиваний изменено на: 15',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=settings)
        elif call.data == '20':
            edit_card(call.message.chat.id, 'co_solves_per_one', 1, 20)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_co_per')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Количество прорешиваний изменено на: 20',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=settings)
        elif call.data == 'Own':
            count = count_of_cards(call.message.chat.id)
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Введите желаемое значение:', parse_mode="html".format(call.message.chat.id), reply_markup=None)
            bot.register_next_step_handler(msg, wanted_count, count)
        elif call.data == 'All':
            count = count_of_cards(call.message.chat.id)
            edit_card(call.message.chat.id, 'co_solves_per_one', 1, count)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_co_per')
            markup.add(button1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Количество прорешиваний изменено на: {count}',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=settings)
        elif call.data == 'come_back_into_settings':
            count_per_ses = int(show_the_first_string(call.message.chat.id)[0][7])
            mode = view_mode(call.message.chat.id)
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton("Изменить количество карточек за раз", callback_data='change_co_per')
            button2 = types.InlineKeyboardButton("Изменить режим", callback_data='change_mode')
            button3 = types.InlineKeyboardButton("Вернуться", callback_data='go_to_main_menu')
            markup.add(button1)
            markup.add(button2)
            markup.add(button3)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'<U><b>Настройки:</b></U>\n\n<b>• Количество карточек за сессию:</b> {count_per_ses}\n<i>(учитывается, если число карточек > или = {count_per_ses})</i>\n\n<b>• Режим карточек:</b> {mode}',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
            bot.callback_query_handler(func=settings)
        elif call.data == 'standart_mode':
            result = show_the_first_string(call.message.chat.id)
            # Если режим уже такой
            if (int(result[0][8]) == 0):
                markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_mode')
                markup.add(button1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=f'Этот режим является вашим текущим',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
                bot.callback_query_handler(func=settings)
            # Если режим нужно поменять
            elif (int(result[0][8]) == 1):
                edit_card(call.message.chat.id, 'mode', 1, 0)
                mode = view_mode(call.message.chat.id)
                markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_mode')
                markup.add(button1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'<b>Режим успешно изменен на:</b> \n{mode}',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
                bot.callback_query_handler(func=settings)
        elif call.data == 'revers_mode':
            result = show_the_first_string(call.message.chat.id)
            if (int(result[0][8]) == 1):
                markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_mode')
                markup.add(button1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Этот режим является вашим текущим',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
                bot.callback_query_handler(func=settings)
            elif (int(result[0][8]) == 0):
                edit_card(call.message.chat.id, 'mode', 1, 1)
                mode = view_mode(call.message.chat.id)
                markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_mode')
                markup.add(button1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'<b>Режим успешно изменен на:</b> \n{mode}',parse_mode="html".format(call.message.chat.id), reply_markup=markup)
                bot.callback_query_handler(func=settings)
# Вспомогательная функция для wanted_count
def wanted_count(message, count):
    try:
        wanted_count = int(message.text)
    except:
        bot.send_message(message.chat.id, text="Ошибка записи (число карточек должно быть числом)")
        return
    if (int(wanted_count) < 1):
        bot.send_message(message.chat.id, text="Желаемое значение не может быть меньше нуля или равно ему")
        return
    try:
        edit_card(message.chat.id, 'co_solves_per_one', 1, wanted_count)
    except:
        bot.send_message(message.chat.id, text="Ошибка записи")
        return
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Вернуться", callback_data='change_co_per')
    markup.add(button1)
    bot.send_message(message.chat.id, text=f'Количество прорешиваний изменено на: {wanted_count}',parse_mode="html".format(message.chat.id), reply_markup=markup)
    bot.callback_query_handler(func=settings)
# inline функция с началом решения карточек чтобы был цикл

def start_solving(mes):
    result = show_the_first_string(mes)
    mode = int(result[0][8])
    if (int(result[0][7]) > count_of_cards(mes)):
        choice_count = count_of_cards(mes)
    else:
        choice_count = int(result[0][7])
    # eval Она принимает строку и интерпретирует ее как выражение Python
    sorted_matrix = eval(show_the_first_string(mes)[0][11])
    sol_help = int((show_card_by_number_of_row(mes, 1))[10])
    if (choice_count > sol_help):
        # Берем номер строки и так как нам надо чтобы через кнопку она
        # предавалась, то делаем как делали ранее
        number_of_string = sorted_matrix[sol_help][0]
        callback_data1 = f'button_pressed_flip:{number_of_string}'
        callback_data2 = f'button_pressed_stop:'
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Перевернуть", callback_data=callback_data1)
        button2 = types.InlineKeyboardButton("Закончить", callback_data=callback_data2)
        markup.add(button1)
        markup.add(button2)
        if (mode == 0):
            bot.send_message(mes, f'{sol_help + 1}) {sorted_matrix[sol_help][4]}', reply_markup=markup)
            bot.callback_query_handler(func=inline_button_after_edit_deck)
        elif (mode == 1):
            bot.send_message(mes, f'{sol_help + 1}) {sorted_matrix[sol_help][5]}', reply_markup=markup)
            bot.callback_query_handler(func=inline_button_after_edit_deck)
        else:
            bot.send_message(chat_id=chat_id, text=f'Режим не определен, ошибка\n(обратитесь за помощью к @kurillccc)')
            print("Ошибка определения режима")
    else:
        if (sol_help == 0):
            bot.send_message(mes, f'Сессия завершена, Вы решили {sol_help} карточек\n(Прошу обратить внимание, что выбранное Вами число карточек за сессию равно 0, поэтому Вы не увидели ни одной карточки)', reply_markup=None)
        else:
            bot.send_message(mes, f'Сессия завершена, Вы решили {sol_help} карточек', reply_markup=None)
        pass_value(mes, 0, 1, 'sol_help')
        return
###########################################################
# Специальная функция, чтобы передавать параметр - номер строки
# далее просто достаем из call.data этот параметр
@bot.callback_query_handler(func=lambda call: True)
def inline_button_after_edit_deck(call):
    sol_help = int((show_card_by_number_of_row(call.message.chat.id, 1))[10]) + 1
    chat_id = call.message.chat.id
    if call.data.startswith('button_pressed_del:'):
        # получаем число из параметра callback_data
        number_of_string = int(call.data.split(':')[1])
        dell_card_by_number(chat_id, number_of_string)
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Вернуться", callback_data='come_back')
        markup.add(button1)
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f'Карточка успешно удалена', reply_markup=markup)
        bot.callback_query_handler(func=actions_with_cards)
    elif call.data.startswith('button_pressed_edit:'):
        # получаем число из параметра callback_data
        number_of_string = int(call.data.split(':')[1])
        msg = bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='Введите первое слово:', reply_markup=None)
        bot.register_next_step_handler(msg, edit_the_card_new_1, number_of_string)
    elif call.data.startswith('button_pressed_flip:'):
        # получаем число из параметра callback_data
        number_of_string = int(call.data.split(':')[1])
        callback_data1 = f'button_pressed_bad:{number_of_string}'
        callback_data2 = f'button_pressed_normal:{number_of_string}'
        callback_data3 = f'button_pressed_good:{number_of_string}'
        callback_data4 = f'button_pressed_great:{number_of_string}'
        callback_data5 = f'button_pressed_stop:'
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("🔴 Плохо", callback_data=callback_data1)
        button2 = types.InlineKeyboardButton("🟠 Трудно", callback_data=callback_data2)
        button3 = types.InlineKeyboardButton("🔵 Хорошо", callback_data=callback_data3)
        button4 = types.InlineKeyboardButton("🟢 Отлично", callback_data=callback_data4)
        button5 = types.InlineKeyboardButton("Закончить", callback_data=callback_data5)
        markup.add(button1, button2, button3)
        markup.add(button4)
        markup.add(button5)
        # Смотрим mode и получаем нашу строку
        row = show_card_by_number_of_row(chat_id, number_of_string)
        mode = int((show_the_first_string(chat_id))[0][8])
        if (mode == 0):
            bot.edit_message_text(chat_id=chat_id,message_id=call.message.message_id,text=f'{sol_help}) {row[4]} - {row[5]}', reply_markup=markup)
            bot.callback_query_handler(func=inline_button_after_edit_deck)
        elif (mode == 1):
            bot.edit_message_text(chat_id=chat_id,message_id=call.message.message_id,text=f'{sol_help}) {row[5]} - {row[4]}', reply_markup=markup)
            bot.callback_query_handler(func=inline_button_after_edit_deck)
        else:
            bot.send_message(chat_id=chat_id, text=f'Режим не определен, ошибка\n(обратитесь за помощью к @kurillccc)')
            print("Ошибка определения режима")
    elif call.data.startswith('button_pressed_stop:'):
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f'Сессия завершена предварительно, Вы решили {sol_help-1} карточек', reply_markup=None)
        pass_value(chat_id, 0, 1, 'sol_help')
        return
    # Кружочки то есть оцениваем то как решили слово
#🔴
    elif call.data.startswith('button_pressed_bad:'):
        number_of_string = int(call.data.split(':')[1])
        # смотрим очки чтобы сложить или вычесть
        result = int((show_card_by_number_of_row(chat_id, number_of_string)[9]))
        result -= 10
        pass_value(chat_id, result, number_of_string, 'point')
        sol_help = int((show_card_by_number_of_row(chat_id, 1))[10])
        sol_help += 1
        pass_value(chat_id, sol_help, 1, 'sol_help')
        count_of_solves = int((show_card_by_number_of_row(chat_id, 1))[6])
        count_of_solves += 1
        pass_value(call.message.chat.id, count_of_solves, 1, 'count_of_solves')
        bot.delete_message(chat_id, call.message.message_id)
        start_solving(chat_id)
 #🟠
    elif call.data.startswith('button_pressed_normal:'):
        number_of_string = int(call.data.split(':')[1])
        # смотрим очки чтобы сложить или вычесть
        result = int((show_card_by_number_of_row(chat_id, number_of_string)[9]))
        result -= 5
        pass_value(chat_id, result, number_of_string, 'point')
        sol_help = int((show_card_by_number_of_row(chat_id, 1))[10])
        sol_help += 1
        pass_value(chat_id, sol_help, 1, 'sol_help')
        count_of_solves = int((show_card_by_number_of_row(chat_id, 1))[6])
        count_of_solves += 1
        pass_value(call.message.chat.id, count_of_solves, 1, 'count_of_solves')
        bot.delete_message(chat_id, call.message.message_id)
        start_solving(chat_id)
#🔵
    elif call.data.startswith('button_pressed_good:'):
        number_of_string = int(call.data.split(':')[1])
        # смотрим очки чтобы сложить или вычесть
        result = int((show_card_by_number_of_row(chat_id, number_of_string)[9]))
        result += 5
        pass_value(chat_id, result, number_of_string, 'point')
        sol_help = int((show_card_by_number_of_row(chat_id, 1))[10])
        sol_help += 1
        pass_value(chat_id, sol_help, 1, 'sol_help')
        count_of_solves = int((show_card_by_number_of_row(chat_id, 1))[6])
        count_of_solves += 1
        pass_value(call.message.chat.id, count_of_solves, 1, 'count_of_solves')
        bot.delete_message(chat_id, call.message.message_id)
        start_solving(chat_id)
#🟢
    elif call.data.startswith('button_pressed_great:'):
        number_of_string = int(call.data.split(':')[1])
        # смотрим очки чтобы сложить или вычесть
        result = int((show_card_by_number_of_row(chat_id, number_of_string)[9]))
        result += 10
        pass_value(chat_id, result, number_of_string, 'point')
        sol_help = int((show_card_by_number_of_row(chat_id, 1))[10])
        sol_help += 1
        pass_value(chat_id, sol_help, 1, 'sol_help')
        count_of_solves = int((show_card_by_number_of_row(chat_id, 1))[6])
        count_of_solves += 1
        pass_value(call.message.chat.id, count_of_solves, 1, 'count_of_solves')
        bot.delete_message(chat_id, call.message.message_id)
        start_solving(chat_id)
###########################################
bot.infinity_polling()