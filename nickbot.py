import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import apiai
import json
DialogFlow_TELEBOT_API_TOKEN = '58395c6273454d75a68116451c2002b6'
DialogFlow_SMALLTALK_API_TOKEN = "368f30714cb54bf499df02386bce9729"
TG_TOKEN_BOT = '972319967:AAHKtNOYFR8eKZfmClHURdjKpbhgdNb1C3k'

user_hero_db = 'nvlchrlzijfvsk'
name_hero_db = 'd6ub309hbsvm8'
psw_hero_db = 'e5d6b2abd2ee59f765e8f4499f97b0970dbd98d0a4f7532c5131483196d90812'
host_hero_db = 'ec2-54-246-92-116.eu-west-1.compute.amazonaws.com'
#ACCESS_TO_HEROKU_DB = 'postgresql://{}:{}@{}:5432/{}'.format(user_hero_db, psw_hero_db, host_hero_db, name_hero_db)
ACCESS_TO_HEROKU_DB = 'postgres://nvlchrlzijfvsk:e5d6b2abd2ee59f765e8f4499f97b0970dbd98d0a4f7532c5131483196d90812@ec2-54-246-92-116.eu-west-1.compute.amazonaws.com:5432/d6ub309hbsvm8'
ACCESS_TO_LOCAL_DB = 'postgresql://postgres:13b1998g@localhost/postgres'

def send_message_dflow(message):#работа с dialogflow
    request = apiai.ApiAI(DialogFlow_TELEBOT_API_TOKEN).text_request()#подключиилсь к пользовательскому dialogflow и собираемся отправить ему запрос
    request.lang = 'ru'
    request.session_id = 'session_1'
    request.query = message #кладем в запрос текс сообщения ползователя
    response = json.loads(request.getresponse().read().decode('utf-8'))
    return response

def do_start(bot: Bot, update: Update):#настройки команды бота /start
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Привет, напиши номер группы и я покажу все пары этой группы в понедельник',
    )

def get_info_from_db(num_of_group):
    engine = create_engine(ACCESS_TO_HEROKU_DB)
    base = declarative_base()

    class schedule(base):#создание таблицы для получения информации из базы данных
        __tablename__ = '{}'.format(num_of_group)
        id = Column(Integer, primary_key=True)
        time = Column(String)
        monday = Column(String)
        tuesday = Column(String)
        wednesday = Column(String)
        thursday = Column(String)
        friday = Column(String)
        saturday = Column(String)

    base.metadata.create_all(engine)  # бд
    session = sessionmaker(bind=engine)()  # бд

    qMonday = session.query(*[schedule.monday]).all()  # получения всей информации из колонки понедельник таблицы бд
    answer = qMonday[0].monday + ' ' + qMonday[1].monday # а эти нан и что? qMonday[2].monday + ' ' + qMonday[3].monday
    return answer

def do_answer(bot: Bot, update: Update):#бот читает новое сообщение и отвечает на него обратившись сначала к бд
    text = update.message.text#чтение сообщение пользователя
    response_dialog_flow = send_message_dflow(text)#отправляю сообщение пользователя на dialogflow

    if response_dialog_flow['result']['action'] == 'question_along_a_schedule' and \
            response_dialog_flow['result']['parameters']['number'] != '' and \
            response_dialog_flow['result']['parameters']['degree_of_education'] != '':
        num = response_dialog_flow['result']['parameters']['number']
        deg = response_dialog_flow['result']['parameters']['degree_of_education']
        num_of_group = deg + '_' + num
        bot_answer = get_info_from_db( num_of_group)
    else:
        bot_answer = response_dialog_flow['result']['fulfillment']['speech']
    bot.send_message(
        chat_id=update.message.chat_id,
        text=bot_answer,
    )

while True:
    bot = Bot(#создание бота
        token=TG_TOKEN_BOT,
        base_url="https://telegg.ru/orig/bot",
    )
    updater= Updater(
        bot=bot,
    )
    start_handler = CommandHandler('start', do_start)#загрузиил команду
    updater.dispatcher.add_handler(start_handler)#добавили команду боту

    message_handler = MessageHandler(Filters.text, do_answer)#загрузиил ответы
    updater.dispatcher.add_handler(message_handler)#добавили ответы боту

    updater.start_polling()
    updater.idle()
