import telebot
import traceback

from itertools import zip_longest
from telebot import TeleBot, types
from telebot import TeleBot, types
from modules.management_func import *

token = ''
bot = telebot.TeleBot(token)
id_send = '-1001884350546' # В какой чат отправить информацию об использовании
administrator = 'kurillccc' # Кого не учитываем при отправке

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
