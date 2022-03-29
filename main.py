import telebot
import re
import sqlite3

conn = sqlite3.connect('db.db', check_same_thread=False)
with open('token.txt', 'r') as f:
    _token = f.readline()
bot = telebot.TeleBot(_token)


day_of_week_dict = {'monday': 'понедельник', 'tuesday':'вторник', 'wednesday': 'среду',
                    'thursday': 'четверг', 'friday': 'пятницу', 'saturday': 'субботу', 'sunday': 'воскресенье'}
day_of_week = None
def insert_new_time(conn, user_name: str, start_time: str, last_time: str, day_of_week):
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO time_table (user_name, start_time, last_time, day_of_week, current) VALUES (?, ?, ?, ?, ?)',
                   (user_name, start_time, last_time, day_of_week, True))
    conn.commit()
def select_times(conn, day_of_week, user_name=None, current=False):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """

    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM time_table where user_name="{user_name}" and day_of_week="{day_of_week}"')

    rows = cursor.fetchall()
    if len(rows)<=1:
        return rows
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
       '1) Чтобы добавить новое время на определенный день недели, нажми /add.\n' +
       '2) Чтобы проверить нынешние времена на каждый день недели нажми /check.\n' +
       '3) Чтобы подтверить изменения на ближайшую неделю, нажми /confirm.\n' +
       '4) если случайно добавил лишний день, его можно удалить при помощи /delete.',
       reply_markup=keyboard
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
        'Выбери дни на следующей неделе, когда можешь играть:',
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
   data = query.data
   if data.startswith('add-'):
       add_possibility(query)
def add_possibility(query):
   bot.answer_callback_query(query.id)
   send_added_result(query)

def send_added_result(query):
   message = query.message
   global day_of_week
   day_of_week = str(query.data).split('-')[-1]
   us_name = message.chat.username
   previous_times = select_times(conn, day_of_week, us_name)
   if len(previous_times)==1:
       previous_time = previous_times[0]
       bot.send_message(
           message.chat.id, f'Выбирай время на {day_of_week_dict[day_of_week]}. \n' +
           'Формат - "10:44-13:30". \n' +
                            f'Предыдущее время на этот день у тебя было {previous_time[1]}-{previous_time[2]},' +
                            ' если устраивает, можешь не менять.',
           # reply_markup=get_update_keyboard(),
           # parse_mode='HTML'
       )
   else:
       bot.send_message(
           message.chat.id, f'В какое время ты можешь играть в {day_of_week_dict[day_of_week]}? \n' +
                            'формат, например "10:44-13:30" \n',
       )

def get_update_keyboard():
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.row(
       telebot.types.InlineKeyboardButton(
           'Сохранить предыдущее время?',
           callback_data='return_default_time'
       ),
   )
   return keyboard

@bot.message_handler(content_types=["text"])
def handle_text(message):
    pattern = '\d\d:\d\d-\d\d:\d\d'
    if re.fullmatch(pattern, message.text):
        global day_of_week
        us_name = message.from_user.username
        start_time = re.findall('\d\d:\d\d', message.text)[0]
        last_time = re.findall('\d\d:\d\d', message.text)[-1]
        if day_of_week is not None:
            insert_new_time(conn, us_name, start_time, last_time, day_of_week)
            bot.send_message(message.chat.id, f'Сохранили: в {day_of_week_dict[day_of_week]} ты можешь в с {start_time} до {last_time}')
        else:
            bot.send_message(message.chat.id,
                             f'Сначала выбери день недели, а потом уже пиши временной промежуток')
    else:
        bot.send_message(message.chat.id, 'не могу прочитать, напиши еще раз:(')

@bot.message_handler(commands=['check'])
def add_command(message):
    us_name = message.chat.username
    bot.send_message(
        message.chat.id,
        'Выбери дни на следующей неделе, когда можешь играть:',
    )
# Запускаем бота
bot.polling(none_stop=True, interval=0)