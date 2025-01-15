import sqlite3

table_with_mailling_list = 'maillig_list'

conn = sqlite3.connect('BaseD_anki.db', check_same_thread=False)
cursor = conn.cursor()

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
