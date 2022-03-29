import telebot
import re
import sqlite3

conn = sqlite3.connect('db.db', check_same_thread=False)
cursor = conn.cursor()
with open('token.txt', 'r') as f:
    _token = f.readline()
bot = telebot.TeleBot(_token)


day_of_week_dict = {'monday': 'понедельник', 'tuesday':'вторник', 'wednesday': 'среду',
                    'thursday': 'четверг', 'friday': 'пятницу', 'saturday': 'субботу', 'sunday': 'воскресенье'}
day_of_week = None
def db_table_val(user_id: int, user_surname: str, start_time: str, last_time: str, day_of_week: str):
    cursor.execute('INSERT OR REPLACE INTO time_table (user_id, user_surname, start_time, last_time, day_of_week) VALUES (?, ?, ?, ?, ?)', (user_id, user_surname, start_time, last_time, day_of_week))
    conn.commit()
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
           'Message the developer', url='telegram.me/kurbobo'
       )
   )
   bot.send_message(
       message.chat.id,
       '1) Чтобы добавить новое время на определенный день недели, нажми /add.\n' +
       '2) Чтобы проверить нынешние времена на каждый день недели нажми /check.\n' +
       '3) Чтобы подтверить изменения на ближайшую неделю, нажми /confirm.\n',
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
   bot.send_message(
       message.chat.id, f'В какое время ты можешь играть в {day_of_week_dict[day_of_week]}? \n'+
       'формат, например "10:44-13:30"',
       reply_markup=get_update_keyboard(),
       parse_mode='HTML'
   )

def get_update_keyboard():
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.row(
       telebot.types.InlineKeyboardButton(
           'Предыдущее время было: ',
           callback_data='return_default_time'
       ),
   )
   return keyboard

@bot.message_handler(content_types=["text"])
def handle_text(message):
    pattern = '\d\d:\d\d-\d\d:\d\d'
    if re.fullmatch(pattern, message.text):
        global day_of_week
        us_id = message.from_user.id
        us_sname = message.from_user.username
        start_time = re.findall('\d\d:\d\d', message.text)[0]
        last_time = re.findall('\d\d:\d\d', message.text)[-1]
        if day_of_week is not None:
            db_table_val(us_id, us_sname, start_time, last_time, day_of_week)
            bot.send_message(message.chat.id, f'Сохранили: в {day_of_week_dict[day_of_week]} ты можешь в с {start_time} до {last_time}')
        else:
            bot.send_message(message.chat.id,
                             f'Сначала выбери день недели, а потом уже пиши временной промежуток')
    else:
        bot.send_message(message.chat.id, 'не могу прочитать, напиши еще раз:(')
# Запускаем бота
bot.polling(none_stop=True, interval=0)