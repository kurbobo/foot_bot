import telebot
import re
import sqlite3
import threading
from time import sleep
from random import randint
from tabulate import tabulate
from pandas import DataFrame
from database import *
from os import remove
import dataframe_image as dfi
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

conn = sqlite3.connect('db.db', check_same_thread=False)
with open('token.txt', 'r') as f:
    _token = f.readline()
bot = telebot.TeleBot(_token)


day_of_week_dict = {'monday': 'понедельник', 'tuesday':'вторник', 'wednesday': 'среду',
                    'thursday': 'четверг', 'friday': 'пятницу', 'saturday': 'субботу', 'sunday': 'воскресенье'}
global_day_of_week = {}
# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Привет, я бот для сборов по футбольчику, если хочешь играть в футбольчик, тебе сюда:) \n' +
                     'Введи /help, чтобы узнать, что я могу!')


@bot.message_handler(commands=['help'])
def help_command(message):
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.add(
       telebot.types.InlineKeyboardButton(
           'Напишите разработчику', url='telegram.me/kurbobo'
       )
   )
   bot.send_message(
       message.chat.id,
       'В пятницу 19:00 начинается  запись расписания новой недели; в воскресенье в 21:00 она заканчивается.\n' +
       'Бот напоминает про начало записи в пятницу 19:00, а также про заполнение таблички в субботу и в воскресенье в 13:00.\n' +
       'Функционал:\n' +
       '1) Чтобы добавить новое время на определенный день недели, нажми /add\n' +
       '2) Чтобы проверить твои актуальные записи на каждый день недели нажми /view\n' +
       '3) Если случайно добавил лишний день, его можно удалить при помощи /delete\n' +
       '4) Чтобы посмотреть общую статистику, нажми /stat\n',
       # '5) если хочешь отменить подтверждение, нажми ',
       reply_markup=keyboard,
       parse_mode='HTML'
   )

@bot.message_handler(commands=['add'])
def add_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('понедельник', callback_data='add-monday'),
        telebot.types.InlineKeyboardButton('вторник', callback_data='add-tuesday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('среда', callback_data='add-wednesday'),
        telebot.types.InlineKeyboardButton('четверг', callback_data='add-thursday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('пятница', callback_data='add-friday'),
        telebot.types.InlineKeyboardButton('суббота', callback_data='add-saturday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('воскресенье', callback_data='add-sunday'),
        # telebot.types.InlineKeyboardButton('суббота', callback_data='get-EUR')
    )

    bot.send_message(
        message.chat.id,
        'Выбери дни на следующей неделе, которые хочешь <b>добавить</b> в расписание:',
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['delete'])
def add_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('понедельник', callback_data='delete-monday'),
        telebot.types.InlineKeyboardButton('вторник', callback_data='delete-tuesday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('среда', callback_data='delete-wednesday'),
        telebot.types.InlineKeyboardButton('четверг', callback_data='delete-thursday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('пятница', callback_data='delete-friday'),
        telebot.types.InlineKeyboardButton('суббота', callback_data='delete-saturday')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('воскресенье', callback_data='delete-sunday'),
        # telebot.types.InlineKeyboardButton('суббота', callback_data='get-EUR')
    )

    bot.send_message(
        message.chat.id,
        'Выбери дни, которые хочешь <b>удалить</b> из расписания:',
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
   data = query.data
   if data.startswith('add-'):
       global_day_of_week[query.message.chat.id] = str(query.data).split('-')[-1]
       add_possibility(query)
   if data=='return_default_time':
       return_default_time(query)
   if data.startswith('delete-'):
       delete_day(query)

def add_possibility(query):
   bot.answer_callback_query(query.id)
   send_added_result(query)

def return_default_time(query):
   global global_day_of_week
   week_day = day_of_week_dict[global_day_of_week[query.message.chat.id]]
   bot.answer_callback_query(query.id)
   update_current_state(query)
   bot.send_message(
       query.message.chat.id, f"Запись на {week_day} сохранена.",
   )

def delete_day(query):
    bot.answer_callback_query(query.id)
    set_current_state_to_false(query)
    day_of_week = str(query.data).split('-')[-1]
    bot.send_message(
        query.message.chat.id, f'Свободное время в {day_of_week_dict[day_of_week]} удалено.',
    )

def update_current_state(query):
    global global_day_of_week
    day_of_week = global_day_of_week[query.message.chat.id]
    user_name = query.message.chat.username
    sql = f''' UPDATE time_table
                  SET current = TRUE
                  WHERE user_name="{user_name}" and day_of_week="{day_of_week}"'''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def set_current_state_to_false(query):
    user_name = query.message.chat.username
    day_of_week = str(query.data).split('-')[-1]
    sql = f''' UPDATE time_table
                  SET current = FALSE
                  WHERE user_name="{user_name}" and day_of_week="{day_of_week}"'''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def send_added_result(query):
   message = query.message
   global global_day_of_week
   day_of_week = global_day_of_week[query.message.chat.id]
   us_name = message.chat.username
   previous_times = select_times(conn, day_of_week, us_name)
   if len(previous_times)==1:
       previous_time = previous_times[0]
       bot.send_message(
           message.chat.id, f'Выбирай время на {day_of_week_dict[day_of_week]}. \n' +
           'Формат - "10:44-13:30". \n' +
                            f'Предыдущее время на этот день у тебя было {previous_time[1]}-{previous_time[2]}.',
           reply_markup=get_update_keyboard(),
           parse_mode='HTML'
       )
   else:
       bot.send_message(
           message.chat.id, f'В какое время ты можешь играть в {day_of_week_dict[day_of_week]}? \n' +
                            'формат, например "10:44-13:30" \n',
       )
   return day_of_week

def get_update_keyboard():
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.row(
       telebot.types.InlineKeyboardButton(
           'Сохранить предыдущее время.',
           callback_data='return_default_time'
       ),
   )
   return keyboard
@bot.message_handler(commands=['view'])
def view(message):
    us_name = message.chat.username
    time_table = select_user_time_table(conn, us_name)
    data_list = []
    for day_data in time_table:
        _, start_time, end_time, day, _, _ = day_data
        data_list.append(f'{day_of_week_dict[day]}: {start_time}-{end_time} &#9745;')
    if len(data_list)>0:
        bot.send_message(
            message.chat.id,
            'Твое свободное время для футбольчика на следующую неделю:\n' + '\n'.join(data_list),
            parse_mode='HTML'
        )
    else:
        bot.send_message(
            message.chat.id,
            'На следующую неделю у тебя пока нет записей, добавь актуальные времена при помощи команды /add.',
            parse_mode='HTML'
        )

@bot.message_handler(commands=['stat'])
def get_statistic(message):
    us_name = message.chat.username
    statistics = get_statistics(conn)
    statistics = [(stat[0].strip(), stat[1]) for stat in statistics]
    statistics_df = DataFrame(statistics, columns=['day', 'count'])
    statistics_df = statistics_df.set_index('day')
    filename = f'stat_{randint(0, 1000)}.png'
    statistics_df = statistics_df.style.set_table_styles([{'selector': '',
                                                           'props': [('border',
                                                                      '3px solid green')]}])
    statistics_df = statistics_df.set_properties(
        **{'text-align': 'center', 'border-color': 'green', 'border-width': 'thin', 'border-style': 'solid'})
    dfi.export(statistics_df, filename)
    bot.send_photo(message.chat.id, open(filename, 'rb'))
    remove(filename)

@bot.message_handler(commands=['full_stat'])
def get_full_statistic(message):
    statistics = get_full_statistics(conn)
    statistics = [tuple(stat[:4]) for stat in statistics]
    statistics_df = DataFrame(statistics,
                              columns=['user_name', 'start_time', 'end_time','day'])
    statistics_df['time'] = statistics_df.apply(lambda x: x['start_time']+'-'+x['end_time'], axis=1)
    statistics_df.drop(columns=['start_time', 'end_time'], inplace=True)
    statistics_df = statistics_df.pivot('user_name', 'day', 'time')
    statistics_df.fillna('-', inplace=True)
    filename = f'full_stat_{randint(0, 1000)}.png'
    statistics_df = statistics_df.style.set_table_styles([{'selector': '',
                                'props': [('border',
                                           '3px solid green')]}])
    statistics_df = statistics_df.set_properties(
        **{'text-align': 'center', 'border-color': 'green', 'border-width': 'thin', 'border-style': 'solid'})
    dfi.export(statistics_df, filename)
    bot.send_photo(message.chat.id, open(filename, 'rb'))
    remove(filename)

@bot.message_handler(content_types=["text"])
def handle_text(message):
    pattern = '\d\d:\d\d-\d\d:\d\d'
    if re.fullmatch(pattern, message.text):
        global global_day_of_week
        day_of_week = global_day_of_week[message.chat.id]
        us_id = message.chat.id
        us_name = message.from_user.username
        from datetime import datetime
        start_time = re.findall('\d\d:\d\d', message.text)[0]
        last_time = re.findall('\d\d:\d\d', message.text)[-1]
        import time
        try:
            start_time_stamp = time.strptime(start_time, '%H:%M')
            last_time_stamp = time.strptime(last_time, '%H:%M')
            if last_time_stamp<=start_time_stamp:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id,
                             f'Некорректный формат времени или некорректный временной интервал, попробуй еще раз.')
        else:
            if day_of_week is not None:
                insert_new_time(conn, us_id, us_name, start_time, last_time, day_of_week)
                bot.send_message(message.chat.id, f'Сохранили: в {day_of_week_dict[day_of_week]} ты можешь с {start_time} до {last_time}')
            else:
                bot.send_message(message.chat.id,
                                 f'Сначала выбери день недели, а потом уже пиши временной промежуток')
    else:
        bot.send_message(message.chat.id, 'не могу прочитать, напиши еще раз:(')

def notifications(conn):
    def make_non_current(conn):
        sql = f''' UPDATE time_table
                          SET current = FALSE'''
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        chat_ids = set(select_users_ids(conn))
        for chat in chat_ids:
            try:
                bot.send_message(chat_id=chat[0], text="Пора заполнять данные на новую неделю!")
            except telebot.apihelper.ApiTelegramException:
                continue

    def ping_users(conn):
        chat_ids = set(select_users_ids(conn))
        for chat in chat_ids:
            try:
                bot.send_message(chat_id=chat[0], text="Напоминаю про заполнение таблички на новую неделю!")
            except telebot.apihelper.ApiTelegramException:
                continue
    schedule.every().friday.at("19:00").do(lambda: make_non_current(conn))
    schedule.every().saturday.at("13:00").do(lambda: ping_users(conn))
    schedule.every().sunday.at("13:00").do(lambda: ping_users(conn))
    while True:
        schedule.run_pending()
        sleep(1)

if __name__=='__main__':
    t = threading.Thread(target=notifications, args=(conn, ))
    t.start()
    # Запускаем бота
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except:
            sleep(10)